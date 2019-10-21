import re
import os
import sys
import glob
from moviepy.editor import *
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
from get_by_type import *

IMAGEMAGICK_BINARY = os.getenv('IMAGEMAGICK_BINARY', 'C:\\Program Files\\ImageMagick-7.0.8-Q16\\magick.exe')
OUTPUT_FDR = "output\\"

class ToPollyMP4:
    def __init__(self, folder):
        self.__path = get_paths_by_typ(folder, "mp4")[0]
        self.__name = re.search("(\w+).mp4",self.__path).group(1)
        self.__folder = folder
    def get_folder(self):
        return self.__folder
    def get_path(self): # gets path to MP4 in folder
        return self.__path
    def get_name(self):
        return self.__name

class ToPollySRT:
    def __init__(self, folder):
        self.__path = get_paths_by_typ(folder, "srt")[0]
        self.__name = re.search("(\w+).srt",self.__path).group(1)
        self.__seq_dict = self.__seqDict(self.__path)
        self.__folder = folder
        self.__n_seq

    def get_name(self):
        return self.__name
    def get_path(self):
        return self.__path
    def get_seq(self,n):
        return self.__seq_dict[n]
    def get_n_seq(self):
        return self.__n_seq
    def get_folder(self):
        return self.__folder
    # def get_dict(self):
    #     return self.__seq_dict

    def __seqDict(self,srt_file): # cut SRT into timestamp dict
        seq_dict={}
        contents=[]
        seq_n = 1
        with open(srt_file, "rt") as f:
            for line in f:
                contents.append(line)
            for line_i in range(0,len(contents)):
                if contents[line_i]==(str(seq_n)+"\n"):
                    matches = re.findall(r"(\d\d:\d\d:\d\d,\d\d\d)",contents[line_i + 1])
                    script_i = 2
                    script = ""
                    while contents[line_i + script_i] != "\n":
                        script += contents[line_i + script_i][:-1] + " "
                        script_i += 1
                    seq_dict[seq_n] = {"script_start": matches[0],
                                       "script": script}
                    seq_n += 1
            self.__n_seq = seq_n - 1 #-1
        return seq_dict

def _polly(output_fdr, file_name, script, voice_id, news):
    session = Session()
    polly = session.client("polly")
    str_frnt = "<speak>"
    str_back = "</speak>"
    if news:
        str_frnt += "<amazon:domain name='news'>"
        str_back = "</amazon:domain>" + str_back
    text = str_frnt + script + str_back

    try:
        response = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=voice_id, Engine="neural", TextType="ssml")
    except (BotoCoreError, ClientError) as error:
        print(error)
        sys.exit(-1)

    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
            output = os.path.join(output_fdr, file_name)
            try:
                with open(output, "wb") as file:
                    file.write(stream.read())
            except IOError as error:
                print(error)
                sys.exit(-1)
    else:
        print("Could not stream audio")
        sys.exit(-1)

def _file_idx(file_name):
    return re.search(r"_(\d\d\d)\.",file_name).group(1)

def cut_MP4(mp4_obj, srt_obj): # returns mp4s in subfolder
    clip = VideoFileClip(mp4_obj.get_path())
    output_fdr = mp4_obj.get_folder() + OUTPUT_FDR
    os.makedirs(output_fdr, exist_ok=True)
    num_seq = srt_obj.get_n_seq()
    for seq_i in range(1, num_seq + 1):#range(0, num_seq)
        script_start = srt_obj.get_seq(seq_i)["script_start"]
        new_clip = None
        if seq_i == num_seq:#num_seq-1
            new_clip = clip.subclip(script_start)
        else:
            next_start = srt_obj.get_seq(seq_i + 1)["script_start"]
            new_clip = clip.subclip(script_start, next_start)
        
        prev_end = script_start
        file_name = mp4_obj.get_name() + "_" + str(seq_i).zfill(3) + ".mp4"
        output_path = output_fdr + file_name
        new_clip.write_videofile(output_path, audio=False)

def to_Polly(srt_obj):# returns mp3s in subfolder
    output_fdr = srt_obj.get_folder() + OUTPUT_FDR
    os.makedirs(output_fdr, exist_ok=True)
    for seq_i in range(1, srt_obj.get_n_seq()+1): #range(0, srt_obj.get_n_seq())
        script = srt_obj.get_seq(seq_i)["script"]
        file_name = srt_obj.get_name() + "_" + str(seq_i).zfill(3) + ".mp3"
        output_path = output_fdr + file_name
        print("Communincating to AWS Polly")
        _polly(output_fdr=output_fdr, file_name=file_name, script=script, voice_id="Brian", news=False)

def composite_MP4(folder, vid_name, title): # returns mp4 in basefolder
    video_res = (1080,720)
    fade_color = [255,255,255]
    vid_clips = sorted(glob.glob(folder + OUTPUT_FDR + "*.mp4"), key=_file_idx)
    aud_clips = sorted(glob.glob(folder + OUTPUT_FDR + "*.mp3"), key=_file_idx)
    title_clip = TextClip(txt=title, size=video_res, method="label", font="Ubuntu-Mono", color="black", bg_color="white", fontsize=103).set_duration("00:00:03").fadeout(duration=1, final_color=fade_color)
    vid_list = [title_clip]
    for i in range(0,len(vid_clips)):
        vid_clip = VideoFileClip(vid_clips[i])
        aud_clip = AudioFileClip(aud_clips[i])
        if (vid_clip.duration < aud_clip.duration):
            vid_clip = vid_clip.set_duration(aud_clip.duration)
        if i==0:
            vid_list.append(vid_clip.set_audio(aud_clip).fadein(duration=1, initial_color=fade_color))
        else:
            vid_list.append(vid_clip.set_audio(aud_clip))

    composite = concatenate_videoclips(vid_list).resize(height=720)
    composite.fps = 30
    composite_path = folder + vid_name + "_comp.mp4"
    composite.write_videofile(composite_path)
    print("Job Complete")

    return composite_path
