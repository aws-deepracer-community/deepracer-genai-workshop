# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

import deepracer
import s3
import yaml


class DeepRacerModel:
    def __init__(self, bucket: str, model_key: str):
        self.bucket = bucket
        self.model_key = model_key

    def __get_track_used_for_training(self, training_metrics_file_key):
        """
        Obtain the track used for training from the eval metrics file.

        Args:
            training_metrics_file_key (string): The S3 key for the training metrics file

        Returns:
            The track used for training. If the track is not found, "unknown" is returned.

        """
        try:
            training_parmas_directory_key = self.model_key
            files = s3.list_files(self.bucket, training_parmas_directory_key)
            for file in files:
                file_key = file["Key"]
                file_name = file_key.split("/")[-1]
                training_metrics_file_name = training_metrics_file_key.split("/")[-1]
                if file_name.endswith(".yaml") and file_name.startswith(
                    "training_params"
                ):
                    training_settings = s3.get_file_content(self.bucket, file_key)
                    if training_metrics_file_name in training_settings:
                        track_id = yaml.safe_load(training_settings)["WORLD_NAME"]
                        track_arn = f"arn:aws:deepracer:us-east-1::track/{track_id}"
                        return deepracer.get_track_name_and_description_from_arn(
                            track_arn
                        )
        except Exception as e:
            print("Could not obtain the track used for training", e)
        return "unknown"

    def __get_track_used_for_evaluation(self, evaluation_metrics_file_key):
        """
        Obtain the track used for evaluation from the eval metrics file.

        Args:
            evaluation_metrics_file_key (string): The S3 key for the evaluation metrics file

        Returns:
            The track used for evaluation. If the track is not found, "unknown" is returned.

        """
        try:
            eval_parmas_directory_key = self.model_key
            files = s3.list_files(self.bucket, eval_parmas_directory_key)
            for file in files:
                file_key = file["Key"]
                file_name = file_key.split("/")[-1]
                evaluation_metrics_file_name = evaluation_metrics_file_key.split("/")[
                    -1
                ]
                if file_name.endswith(".yaml") and file_name.startswith("eval_params"):
                    evaluation_settings = s3.get_file_content(self.bucket, file_key)
                    if evaluation_metrics_file_name in evaluation_settings:
                        track_id = yaml.safe_load(evaluation_settings)["WORLD_NAME"]
                        track_arn = f"arn:aws:deepracer:us-east-1::track/{track_id}"
                        return (
                            deepracer.get_track_name_and_description_from_arn(
                                track_arn
                            ),
                            track_id,
                        )
        except Exception as e:
            print("Could not obtain the track used for evaluation", e)
        return "unknown", track_id

    def __get_top_leaderboard_entry_paginated(self, track_id, next_token=None):
        """
        Get the top leaderboard entry for a given track.

        Args:
            track_id (string): The id of the track.
            next_token (string, optional): The next token to use for pagination. Defaults to None.

        Returns:
            A dictionary containing the next token and the top leaderboard entry.
        """
        if next_token == None:
            response = deepracer.list_leaderboards(max_results=50)
        else:
            response = deepracer.list_leaderboards(
                max_results=50, next_token=next_token
            )
        leaderboards = response["Leaderboards"]
        next_token = None
        if "NextToken" in response:
            next_token = response["NextToken"]

        for leaderboard in leaderboards:
            if track_id in leaderboard["TrackArn"]:
                submissions = deepracer.list_leaderboard_submissions(
                    leaderboard_arn=leaderboard["Arn"]
                )

                top_entry = submissions["LeaderboardSubmissions"][0]
                top_entry_extract = {
                    key: top_entry[key]
                    for key in top_entry.keys()
                    & {
                        "AvgLapTime",
                        "BestLapTime",
                        "AvgResets",
                        "CollisionCount",
                        "OffTrackCount",
                        "ResetCount",
                    }
                }
                return {"NextToken": None, "Entry": top_entry_extract}
        return {"NextToken": next_token, "Entry": {}}

    def __get_fastest_lap_time_by_track_name(self, track_id):
        """
        Get the fastest lap time for a given track.

        Args:
            track_id (string): The id of the track.

        Returns:
            The fastest lap time for the given track.
        """
        response = self.__get_top_leaderboard_entry_paginated(track_id, next_token=None)
        while response["NextToken"] != None and response["Entry"] == {}:
            response = self.__get_top_leaderboard_entry_paginated(
                track_id, next_token=response["NextToken"]
            )
        return response["Entry"]

    def get_reward_function(self) -> str:
        """
        Get the reward function from the extracted model file.

        Returns:
            The reward function.
        """
        try:
            reward_function_file_path = "reward_function.py"

            file_key = f"{self.model_key}/{reward_function_file_path}"
            reward_function = s3.get_file_content(self.bucket, file_key)
            return reward_function
        except Exception as e:
            print("Could not obtain the reward function", e)
        return "unknown"

    def get_hyper_parameters(self):
        """
        Get the hyperparameters used for training the model.

        Returns:
            The hyperparameters used for training the model.
        """
        try:
            hyperparameters_file_path = "ip/hyperparameters.json"
            file_key = f"{self.model_key}/{hyperparameters_file_path}"
            hyperparameters = json.loads(s3.get_file_content(self.bucket, file_key))
            return hyperparameters
        except Exception as e:
            print("Could not obtain the hyperparameters", e)
        return "unknown"

    def get_model_meta_data(self):
        """
        Get the meta data used for training the model.

        Returns:
            The meta data used for training the model.
        """
        try:
            model_meta_data_json_file_path = "model/model_metadata.json"

            file_key = f"{self.model_key}/{model_meta_data_json_file_path}"
            model_metadata = json.loads(s3.get_file_content(self.bucket, file_key))
            return {
                key: model_metadata[key]
                for key in model_metadata.keys()
                & {"action_space", "action_space_type", "sensor"}
            }
        except Exception as e:
            print("Could not obtain the hyperparameters", e)
        return "unknown"

    def get_training_metrics(self):
        """
        Get the training metrics used for training the model.

        Returns:
            The training metrics used for training the model.
        """
        try:
            training_metrics_file_path = "metrics/training"
            file_key = f"{self.model_key}/{training_metrics_file_path}"
            training_metric_files = s3.list_files(self.bucket, file_key)
            for training_metric_file in training_metric_files:
                training_metric_file_key = training_metric_file["Key"]
                if training_metric_file_key.endswith(".json"):
                    training_metrics = json.loads(
                        s3.get_file_content(self.bucket, training_metric_file_key)
                    )["metrics"]
                    last_evaluation_result_per_iteration = {}
                    for section in training_metrics:
                        if section["phase"] == "evaluation":
                            last_evaluation_result_per_iteration[section["episode"]] = {
                                key: section[key]
                                for key in section.keys()
                                & {
                                    "elapsed_time_in_milliseconds",
                                    "completion_percentage",
                                    "reward_score",
                                    "episode",
                                    "episode_status",
                                }
                            }
                    track = "unknown"
                    try:
                        track = self.__get_track_used_for_training(
                            training_metrics_file_path
                        )
                    except Exception as e:
                        print(f"Could not get track for training: {e}")

                    return {
                        "metrics": list(last_evaluation_result_per_iteration.values()),
                        "track": track,
                    }
        except Exception as e:
            print("Could not obtain training metrics", e)
        return {"metrics": "unknown", "track": "unknown"}

    def get_evaluation_metrics(self):
        """
        Get the evaluation metrics used for training the model.

        Returns:
            The evaluation metrics used for training the model.
        """

        try:
            evaluation_metrics_file_path = "metrics/evaluation"
            file_key = f"{self.model_key}/{evaluation_metrics_file_path}"
            evaluation_metric_files = s3.list_files(self.bucket, file_key)
            for evaluation_metrics_file in evaluation_metric_files:
                evaluation_metrics_file_key = evaluation_metrics_file["Key"]
                if evaluation_metrics_file_key.endswith(".json"):
                    evaluation_metrics = json.loads(
                        s3.get_file_content(self.bucket, evaluation_metrics_file_key)
                    )["metrics"]
                    stripped_evaluation_metrics = []
                    for evaluation_metric in evaluation_metrics:
                        stripped_evaluation_metrics.append(
                            {
                                key: evaluation_metric[key]
                                for key in evaluation_metric.keys()
                                & {
                                    "completion_percentage",
                                    "elapsed_time_in_milliseconds",
                                    "episode_status",
                                    "crash_count",
                                    "reset_count",
                                    "off_track_count",
                                }
                            }
                        )
                    track = "unknown"
                    try:
                        track, track_id = self.__get_track_used_for_evaluation(
                            evaluation_metrics_file_key
                        )
                    except Exception as e:
                        print("Could not obtain track used for evaluation", e)

                    fastest_lap_time = "unknown"
                    try:
                        track_name = track["Name"]
                        fastest_lap_time = self.__get_fastest_lap_time_by_track_name(
                            track_id
                        )
                    except Exception as e:
                        print("Could not obtain fastest lap time by others", e)

                    return {
                        "metrics": stripped_evaluation_metrics,
                        "track": track,
                        "fastest_lap_time_by_others_in_milliseconds": fastest_lap_time,
                    }
        except Exception as e:
            print("Could not obtain evaluation metrics", e)
        return {
            "metrics": "unknown",
            "track": "unknown",
            "fastest_lap_time_by_others_in_milliseconds": "unknown",
        }

    def get_track_meta_data(self):
        return "Track difficulty is an integer ranging from 100 to 1, where 1 is the hardest"
