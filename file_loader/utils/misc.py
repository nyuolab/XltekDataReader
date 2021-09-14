import os
import cv2
import json
import collections
import numpy as np


def load_json(load_path):
    with open(load_path, 'r') as f:
        json_file = json.load(
            f, object_pairs_hook=collections.OrderedDict
        )
    return json_file


def frame_filetime(vtc_loader, path):
    video_file_lst = []
    filetime_lst = []

    file_list = vtc_loader.data['video_toc_entry']['video_filename']
    start_list = vtc_loader.data['video_toc_entry']['filetime_starttime']
    end_list = vtc_loader.data['video_toc_entry']['filetime_endtime']

    for vid_f, start_time, end_time in zip(file_list, start_list, end_list):

        vid_path = os.path.join(path, vid_f)
        vid = cv2.VideoCapture(vid_path)
        total_frames = vid.get(cv2.CAP_PROP_FRAME_COUNT)

        # Use linear interpolation to find filetime,
        # since filetime is a count of ms.
        times = np.linspace(
            start_time,
            end_time,
            int(total_frames),
            dtype=int
        )

        filetime_lst.append(times)
        video_file_lst.append(vid_path)

        vid.release()

    filetime_lst = np.concatenate(filetime_lst)
    return video_file_lst, filetime_lst
