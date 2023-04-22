from PyQt5 import QtCore
from moviepy.editor import concatenate_videoclips
import datetime
from proglog import ProgressBarLogger


class VideoSignal(QtCore.QObject):
    signal_prg = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(str)

    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(object, str)


class MyBarLogger(ProgressBarLogger):
    def __init__(self, signal):
        super(MyBarLogger, self).__init__()
        self.signal = signal

    def bars_callback(self, bar, attr, value, old_value=None):
        if bar == 'frame_index':
            percentage = (value / self.bars[bar]['total']) * 100
            self.signal.emit(int(percentage))


class ProcessVideo(QtCore.QRunnable):

    def __init__(self, video_clips, codec, audio_codec, preset, cores, fps,
                 bitrate, audio, extension, destination, file_name):
        super(ProcessVideo, self).__init__()

        self.terminate = False
        self.signals = VideoSignal()
        self.codec = codec
        self.audio_codec = audio_codec
        self.preset = preset
        self.cores = cores
        self.fps = fps
        self.bitrate = bitrate
        self.audio = audio
        self.video_clips = video_clips
        self.extension = extension
        self.destination = destination
        self.file_name = file_name.split('/')[-1].split('.')[0]
        self.logger = MyBarLogger(self.signals.signal_prg)

    @QtCore.pyqtSlot()
    def run(self):
        try:
            for j in range(len(self.video_clips)):
                video_file_name = self.destination + '/' + str(j + 1) + '--' + \
                                  self.file_name + '.' + self.extension.lower()
                self.video_clips[j].write_videofile(video_file_name,
                                                    codec=self.codec,
                                                    audio_codec=self.audio_codec,
                                                    preset=self.preset, threads=self.cores,
                                                    fps=self.fps, bitrate=self.bitrate, audio=self.audio,
                                                    logger=self.logger
                                                    )
                self.video_clips[j].close()
                self.signals.signal_prg.emit(int(round(((j + 1) / len(self.video_clips)) * 100)))
            self.signals.finished.emit('ok')
        except Exception as e:
            print('error process video', repr(e))
            self.signals.finished.emit('error')


class ExtractSignal(QtCore.QObject):
    signal_prg = QtCore.pyqtSignal(str, int, int)
    finished = QtCore.pyqtSignal(str, list)

    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(object, str)


class ExtractClips(QtCore.QRunnable):

    def __init__(self, times, cut_list, video, forward, backward, gap, starting_sub, ending_sub):
        super(ExtractClips, self).__init__()
        self.terminate = False
        self.signals = ExtractSignal()
        self.cut_list = cut_list
        self.times = times
        self.video = video
        self.forward = forward
        self.backward = backward
        self.gap = gap
        self.starting_subtitle = starting_sub
        self.ending_subtitle = ending_sub

    @QtCore.pyqtSlot()
    def run(self):
        try:
            video_clips = []
            # print('enter2')
            for t in self.cut_list:
                start = self.starting_subtitle + t[0]
                end = self.starting_subtitle + t[1] + 1
                clips = []
                time_zero = datetime.datetime.strptime('00:00:00', '%H:%M:%S')
                history = None
                final_cuts = []
                for i in range(start, end):
                    d1 = self.times[i][0]
                    if d1 - datetime.timedelta(seconds=self.forward) > time_zero:
                        d1 = self.times[i][0] - datetime.timedelta(seconds=self.backward)
                    d2 = self.times[i][1] + datetime.timedelta(seconds=self.forward)
                    if i - start - 1 >= 0:
                        if (d1 - history) < datetime.timedelta(seconds=self.gap):
                            if i + 1 == end:
                                final_cuts[-1][1] = datetime.datetime.strftime(d2 +
                                                                               datetime.timedelta(seconds=self.forward),
                                                                               '%H:%M:%S,%f')[:-3]
                            else:
                                final_cuts[-1][1] = datetime.datetime.strftime(d2, '%H:%M:%S,%f')[:-3]

                            history = d2
                            continue
                    history = d2
                    startt = datetime.datetime.strftime(d1, '%H:%M:%S,%f')[:-3]
                    endd = datetime.datetime.strftime(d2, '%H:%M:%S,%f')[:-3]
                    final_cuts.append([startt, endd])
                for c in final_cuts:
                    clip = self.video.subclip(c[0], c[1])
                    clips.append(clip)
                final_clip = concatenate_videoclips(clips)
                video_clips.append(final_clip)
            self.signals.finished.emit('ok', video_clips)
        except Exception as e:
            print('error extract clip', repr(e))
            self.signals.finished.emit('error', None)
