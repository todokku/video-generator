'''
video.json = {
        "title" : "YOUTUBE TITLE HERE",
        "description" : "YOUTUBE DESCRIPTION HERE"
    }

video.json = {
        "title" : "YOUTUBE TITLE HERE",
        "description" : "YOUTUBE DESCRIPTION HERE",
        "meta" : {
            video_i: [int] index,
            status: [string] "json" || "mp4" || "srt" || "post",
            last_edit: [int] last edit time for json/mp4 (pre_polly),
            pre_polly_id: [string] youtube_video_id,
            post_polly_id: [string] youtube_video_id,
        }
    }

videos.json = {
        "log" : {
            status: [string] "pre" || "post"
            changes: int[] indexes,
            nxt_vid_i: [int] n + 1
        },
        "body" : {
            0 : video_dict (from video.json)
            1 : video_dict
                .
                .
                .
            n : video_dict
        }
    }
'''

import os
import json

from checks import valid_vid_json, vids_json_exists, valid_vids_json

class VIDEO_OBJ:
    def __init__(self):
        self.__title=""
        self.__description=""
        self.__meta=dict(
            video_i=0,
            status="",
            last_edit=0,
            pre_polly_id="",
            post_polly_id=""
        )
    def as_dict(self):
        return dict(title=self.__title, description=self.__description, meta=self.__meta)

class VIDEOS_OBJ:
    def __init__(self):
        self.__log=dict(
            status="",
            changes=[],
            nxt_vid_i=0)
        self.__body=dict()
    def as_dict(self):
        return dict(log=self.__log, body=self.__body)

# ALL FUNCTIONS PRESUMES VALID JSON (check logic handled by manager)

def _json_to_dict(path):
    json_dict = {}
    with open(path) as json_f:
        json_dict = json.load(json_f)
    return json_dict

def dict_to_json(vid_dict, path):
    with open(path, "w", encoding="utf-8") as json_f:
        json.dump(vid_dict, json_f, ensure_ascii=False, indent=4)

class VidJSON:
    def __init__(self, path, video_i):
        self.__path = path
        self.__dict = self.__to_dict(path, video_i)
    def __to_dict(self, path, video_i):
        vid_dict = _json_to_dict(path)
        ret_dict = VIDEO_OBJ().as_dict()
        ret_dict["meta"]["video_i"] = video_i
        for key in vid_dict:
            ret_dict[key] = vid_dict[key]
        return ret_dict
    def set_lst_edt(self, value):
        self.__dict["meta"]["last_edit"] = value
    def set_status(self, value):
        self.__dict["meta"]["status"] = value
    def set_pre_id(self, value):
        self.__dict["meta"]["pre_polly_id"] = value
    def set_post_id(self, value):
        self.__dict["meta"]["post_polly_id"] = value
    def get_dict(self):
        return self.__dict
    def get_path(self):
        return self.__path
    def get_video_i(self):
        return self.__dict["meta"]["video_i"]
    def get_status(self):
        return self.__dict["meta"]["status"]
    def get_lst_edt(self):
        return self.__dict["meta"]["last_edit"]
    def get_pre_id(self):
        return self.__dict["meta"]["pre_polly_id"]
    def get_post_id(self):
        return self.__dict["meta"]["post_polly_id"]
    def get_yt_args(self):
        sh_cpy = dict(self.__dict)
        del sh_cpy["meta"]
        sh_cpy["tags"] = [self.get_status()]
        return sh_cpy
    def update_JSON(self):
        return dict_to_json(self.__dict,self.__path)

class VidsJSON:
    def __init__(self, path, fresh):
        self.__path = path
        self.__dict = self.__to_dict(path, fresh)
    def __to_dict(self, path, fresh):
        vids_dict = None
        if fresh:
            vids_dict = VIDEOS_OBJ().as_dict()
        else:
            vids_dict = _json_to_dict(path)
        return vids_dict
    def reset_vid_i(self):
        self.__dict["log"]["nxt_vid_i"] = 0
    def set_status(self, value):
        self.__dict["log"]["status"] = value
    def set_changes(self, value):
        self.__dict["log"]["changes"] = value
    def set_vid_obj(self, vid_obj):
        video_i = str(vid_obj.get_video_i())
        self.__dict["body"][video_i] = vid_obj.get_dict()
        self.__dict["log"]["nxt_vid_i"] = self.__dict["log"]["nxt_vid_i"] + 1
    def get_dict(self):
        return self.__dict
    def to_JSON(self):
        return dict_to_json(self.__dict, self.__path)