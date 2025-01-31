# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

# add python path of PadleDetection to sys.path
parent_path = os.path.abspath(os.path.join(__file__, *([".."] * 2)))
sys.path.insert(0, parent_path)

# ignore warning log
import warnings

warnings.filterwarnings("ignore")

import zmq
import time

import paddle
from paddle.distributed import ParallelEnv
from ppdet.core.workspace import load_config, merge_config
from ppdet.engine import Tracker
from ppdet.utils.check import check_gpu, check_version, check_config
from ppdet.utils.cli import ArgsParser

from ppdet.utils.logger import setup_logger

logger = setup_logger("train")


def parse_args():
    parser = ArgsParser()
    parser.add_argument(
        "--frame_rate", type=int, default=-1, help="Video frame rate for tracking."
    )
    parser.add_argument(
        "--image_dir",
        type=str,
        default=None,
        help="Directory for images to perform inference on.",
    )
    parser.add_argument(
        "--det_results_dir",
        type=str,
        default="",
        help="Directory name for detection results.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="Directory name for output tracking results.",
    )
    parser.add_argument(
        "--save_images", action="store_true", help="Save tracking results (image)."
    )
    parser.add_argument(
        "--save_videos", action="store_true", help="Save tracking results (video)."
    )
    parser.add_argument(
        "--show_image", action="store_true", help="Show tracking results (image)."
    )
    parser.add_argument(
        "--scaled",
        type=bool,
        default=False,
        help="Whether coords after detector outputs are scaled, False in JDE YOLOv3 "
        "True in general detector.",
    )
    parser.add_argument(
        "--draw_threshold",
        type=float,
        default=0.5,
        help="Threshold to reserve the result for visualization.",
    )
    args = parser.parse_args()
    return args


def run(FLAGS, cfg, video_file):
    # build Tracker
    tracker = Tracker(cfg, mode="test")

    # load weights
    if cfg.architecture in ["DeepSORT"]:
        if cfg.det_weights != "None":
            tracker.load_weights_sde(cfg.det_weights, cfg.reid_weights)
        else:
            tracker.load_weights_sde(None, cfg.reid_weights)
    else:
        tracker.load_weights_jde(cfg.weights)

    # inference
    tracker.mot_predict(
        video_file=video_file,
        frame_rate=FLAGS.frame_rate,
        image_dir=FLAGS.image_dir,
        data_type=cfg.metric.lower(),
        model_type=cfg.architecture,
        output_dir=FLAGS.output_dir,
        save_images=FLAGS.save_images,
        save_videos=FLAGS.save_videos,
        show_image=FLAGS.show_image,
        scaled=FLAGS.scaled,
        det_results_dir=FLAGS.det_results_dir,
        draw_threshold=FLAGS.draw_threshold,
    )


def main():
    FLAGS = parse_args()
    cfg = load_config(FLAGS.config)
    merge_config(FLAGS.opt)

    check_config(cfg)
    check_gpu(cfg.use_gpu)
    check_version()

    place = "gpu:{}".format(ParallelEnv().dev_id) if cfg.use_gpu else "cpu"
    place = paddle.set_device(place)

    # Set 0MQ
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    try:
        while True:
            video_file = socket.recv_string()
            print(f"Processing Video: {video_file}")
            run(FLAGS, cfg, video_file)
            # time.sleep(1)
            socket.send(b"Done")
    except KeyboardInterrupt:
        print("W: interrupt received, stopping...")
    finally:
        # clean up
        socket.close()
        context.term()


if __name__ == "__main__":
    main()
