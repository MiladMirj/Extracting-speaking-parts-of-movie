#                                                   https://github.com/MiladMirj
#                                                   https://www.youtube.com/channel/UCpEkH_iYp_dKF89eZylT3yA


"""
This script allows the user to extract speaking parts of a movie based on its subtitle file!
Run 'main.py'  to run the script.

In order to run this script it's required to install the following library.
1- `PyQt5` for handling GUI
2- `moviepy` for processing video

Other modules to run this script:
1- `process` for processing video and audio

 """

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.QtGui import QCursor, QIntValidator
from PyQt5.QtCore import Qt, QThreadPool
from moviepy.editor import VideoFileClip
import datetime
from gui import Ui_MainWindow
import sys
import os
import webbrowser
import multiprocessing
from process import ProcessVideo, ExtractClips
from pathlib import Path

project_path = os.path.dirname(os.path.abspath(__file__))


class MAINGUI(QMainWindow):

    def __init__(self):
        super(MAINGUI, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.save_location = project_path + '\\save path\\'
        Path(self.save_location).mkdir(parents=True, exist_ok=True)
        self.times = None
        self.video = None
        self.all_sub = False
        self.divided = False
        self.ui.btn_load_movie.clicked.connect(self.load_video)
        self.ui.btn_load_subtitle.clicked.connect(self.load_subtitle)
        self.ui.btn_change_location.clicked.connect(self.change_location)
        self.ui.label_save_location.setText(self.save_location)
        self.onlyInt = QIntValidator()
        self.ui.line_start.setValidator(self.onlyInt)
        self.ui.line_end.setValidator(self.onlyInt)
        self.ui.line_gap.setValidator(self.onlyInt)
        self.ui.line_forward.setValidator(self.onlyInt)
        self.ui.line_backward.setValidator(self.onlyInt)
        self.ui.btn_open_folder.clicked.connect(self.open_folder)
        self.thread_counts = multiprocessing.cpu_count()
        self.ui.prg_bar.setValue(0)
        self.ui.label_cores.setText(str(self.thread_counts))
        self.ui.spin_cores.setMaximum(self.thread_counts)
        self.ui.spin_cores.setMinimum(1)
        self.ui.spin_cores.setValue(1)
        self.ui.check_source_res.stateChanged.connect(self.check_source_res_checked)
        self.ui.check_all_lines.stateChanged.connect(self.check_all_lines_checked)
        self.ui.btn_run.clicked.connect(self.run)
        self.threadpool = QThreadPool()
        self.active = True
        self.worker = None
        self.gap = 0
        self.arrow_cursor = QCursor(Qt.ArrowCursor)
        self.forbidden_cursor = QCursor(Qt.ForbiddenCursor)

    def open_folder(self):
        try:
            webbrowser.open(self.save_location)
        except Exception as e:
            print("Can't open folder" + repr(e))

    def update_info(self, info, status):
        if status == 0:
            self.ui.label_info.setStyleSheet('QLabel#label_info{background-color: yellow}')
        elif status == 1:
            self.ui.label_info.setStyleSheet('QLabel#label_info{background-color: white}')

        elif status == 2:
            self.ui.label_info.setStyleSheet('QLabel#label_info{background-color: red; color:white}')

        elif status == 3:
            self.ui.label_info.setStyleSheet('QLabel#label_info{background-color: green; color:white}')

        self.ui.label_info.setText(info)

    def check_source_res_checked(self):
        if self.ui.check_source_res.isChecked():
            if self.video is not None:
                self.ui.line_width.setText(str(self.video.size[0]))
                self.ui.line_height.setText(str(self.video.size[1]))

    def check_all_lines_checked(self):
        if self.ui.check_all_lines.isChecked():
            if self.times is not None:
                self.ui.line_end.setText(str(len(self.times)))
            else:
                print('Load subtitle first')
                # self.ui.check_all_lines.setChecked(0)

    def change_location(self):
        if self.active:
            options = QFileDialog.Options()
            save_location = QFileDialog.getExistingDirectory(self, 'Video File and SRT File Save Location',
                                                             self.save_location,
                                                             options=options)
            if save_location == '':
                return
            self.save_location = save_location
            self.ui.label_save_location.setText(self.save_location)
        else:
            print('Wait to finish!')

    def process_finished(self, status):
        self.active = True
        print('finished end')
        if status == 'ok':
            self.update_info('Finished Processing audio and video ! ', 3)
        else:
            self.update_info('Error Processing audio and video ! ', 2)

        self.ui.btn_run.setCursor(self.arrow_cursor)

    def deliver_video(self, video_clips):
        try:
            cores = self.ui.spin_cores.value()
            codec = self.ui.combo_codec.currentText()
            extension = self.ui.combo_extension.currentText()
            if (codec == 'libx265' and extension == 'WMV') or (codec == 'libx265' and extension == 'AVI'):
                self.update_info('Extension not supported with libx265', 0)
                self.active = True
                self.ui.btn_run.setCursor(self.arrow_cursor)
                return
            if codec == 'rawvideo' and extension != 'AVI':
                self.update_info('Use AVI for rawvidow only', 0)
                self.active = True
                self.ui.btn_run.setCursor(self.arrow_cursor)
                return
            audio = self.ui.check_audio.isChecked()
            if self.ui.combo_fps.currentText() == 'Source FPS':
                fps = None
            else:
                fps = float(self.ui.combo_fps.currentText())
            preset = self.ui.combo_preset.currentText()
            audio_codec = self.ui.combo_codec_audio.currentText()
            if self.ui.combo_bitrate.currentText() == 'Source Bitrate':
                bitrate = None
            else:
                bitrate = self.ui.combo_bitrate.currentText()
            self.worker = ProcessVideo(video_clips, codec, audio_codec, preset,
                                       cores, fps, bitrate, audio, extension,
                                       self.save_location, self.file_name)

            self.worker.signals.finished.connect(self.process_finished)
            self.worker.signals.signal_prg.connect(self.process_prg)
            self.threadpool.start(self.worker)
            self.update_info('Start Processing audio and video ... ', 1)
            self.ui.prg_bar.setValue(0)
        except Exception as e:
            print('Error processing video', repr(e))
            self.update_info('Error Processing audio and video', 2)
            self.active = True
            self.ui.btn_run.setCursor(self.arrow_cursor)

    def process_prg(self, prg):
        self.ui.prg_bar.setValue(prg)

    def run(self):
        if self.active:
            try:
                if self.video is None:
                    self.update_info('Load video first !', 0)
                    return
                if self.times is None:
                    self.update_info('Load subtitle first !', 0)
                    return
                self.starting_subtitle = self.ui.line_start.text()
                if self.starting_subtitle != '':
                    self.starting_subtitle = int(self.starting_subtitle)
                else:
                    self.update_info('Enter starting subtitle !', 0)
                    return
                self.ending_subtitle = self.ui.line_end.text()
                if self.ending_subtitle != '':
                    self.ending_subtitle = int(self.ending_subtitle)
                else:
                    self.update_info('Enter ending subtitle !', 0)
                    return
                if self.starting_subtitle == 0:
                    self.update_info('Start from 1 !', 0)
                    return
                if self.ending_subtitle > len(self.times) or self.starting_subtitle > len(self.times):
                    self.update_info('Ending or starting exceed total lines !', 0)
                    return
                if self.ending_subtitle < self.starting_subtitle:
                    self.update_info('Ending is lower than starting !', 0)
                    return
                self.active = False
                self.ui.btn_run.setCursor(self.forbidden_cursor)
                if self.ui.line_gap.text() != '':
                    self.gap = int(self.ui.line_gap.text())
                else:
                    self.gap = 0
                    self.ui.line_gap.setText('0')
                if self.ui.line_forward.text() != '':
                    self.forward = int(self.ui.line_forward.text())
                else:
                    self.forward = 0
                    self.ui.line_forward.setText('0')

                if self.ui.line_backward.text() != '':
                    self.backward = int(self.ui.line_backward.text())
                else:
                    self.backward = 0
                    self.ui.line_backward.setText('0')
                self.starting_subtitle -= 1
                s = None
                s_history = []
                n_times = []
                time_zero = datetime.datetime.strptime('00:00:00', '%H:%M:%S')
                self.target_width = self.ui.line_width.text()
                if self.target_width != '':
                    self.target_width = int(self.target_width)
                else:
                    self.active = True
                    self.ui.btn_run.setCursor(self.arrow_cursor)
                    self.update_info('Set target width !', 0)
                    return
                self.target_height = self.ui.line_height.text()
                if self.target_height != '':
                    self.target_height = int(self.target_height)
                else:
                    self.update_info('Set target height !', 0)
                    self.active = True
                    self.ui.btn_run.setCursor(self.arrow_cursor)
                    return

                if self.target_height != self.targett_height or self.target_width != self.targett_width:
                    self.video = VideoFileClip(self.file_name,
                                               target_resolution=(self.target_width, self.target_height))
                for i in range(self.starting_subtitle, self.ending_subtitle):

                    if i - self.starting_subtitle == 0:
                        if self.times[i][0] - datetime.timedelta(seconds=self.backward) > time_zero:
                            s = self.times[i][0] - datetime.timedelta(seconds=self.backward)
                        else:
                            s = self.times[i][0]
                    else:

                        if (self.times[i][0] - datetime.timedelta(seconds=self.backward)
                            - self.times[i - 1][1] - datetime.timedelta(seconds=self.forward)) \
                                < datetime.timedelta(seconds=self.gap):

                            s += self.times[i][0] - self.times[i - 1][1] - (self.times[i][0] - self.times[i - 1][1])
                        else:
                            s += self.times[i][0] - self.times[i - 1][1] - datetime.timedelta(seconds=self.forward) - \
                                 datetime.timedelta(seconds=self.backward)

                    n_d1 = self.times[i][0] - s
                    n_d2 = self.times[i][1] - s
                    s_history.append(s)
                    if str(n_d1).split(':')[2] == '00' or '.' not in str(n_d1).split(':')[2]:
                        n_d1 = datetime.datetime.strptime(str(n_d1) + '.00', "%H:%M:%S.%f")
                    else:
                        n_d1 = datetime.datetime.strptime(str(n_d1), "%H:%M:%S.%f")
                    if str(n_d2).split(':')[2] == '00' or '.' not in str(n_d2).split(':')[2]:
                        n_d2 = datetime.datetime.strptime(str(n_d2) + '.00', "%H:%M:%S.%f")
                    else:
                        n_d2 = datetime.datetime.strptime(str(n_d2), "%H:%M:%S.%f")
                    n_times.append([n_d1, n_d2])
                cut_list = []

                if self.ui.check_divide.isChecked():
                    words_each_file = self.ui.line_words_each.text()
                    if words_each_file == '':
                        self.update_info('Set words in each subtitle', 0)
                        return
                    words_each_file = int(words_each_file)
                    k = 0
                    run = True
                    j = 1
                    while run:
                        srt_file_name = self.save_location + '/' + str(j) + '--' + \
                        self.file_name.split('/')[-1].split('.')[0] + '.srt'

                        with open(srt_file_name, 'w') as file:
                            #     for i in range(len(n_times)):
                            len_words = 0
                            start = k
                            first_line = 0
                            first_time = n_times[k][0]
                            for i in range(k, len(n_times)):

                                sub = ''
                                file.write(str(i + 1) + '\n')
                                first_line += 1
                                if j == 1:
                                    file.write(datetime.datetime.strftime(n_times[i][0], '%H:%M:%S,%f')[:-3] + ' --> ' +
                                               datetime.datetime.strftime(n_times[i][1], '%H:%M:%S,%f')[:-3] + '\n')
                                else:
                                    s = n_times[i][0] - first_time + datetime.timedelta(seconds=self.backward)
                                    e = n_times[i][1] - first_time + datetime.timedelta(seconds=self.backward)
                                    if str(n_d1).split(':')[2] == '00' or '.' not in str(s).split(':')[2]:
                                        s = datetime.datetime.strptime(str(s) + '.00', "%H:%M:%S.%f")
                                    else:
                                        s = datetime.datetime.strptime(str(s), "%H:%M:%S.%f")
                                    if str(e).split(':')[2] == '00' or '.' not in str(e).split(':')[2]:
                                        e = datetime.datetime.strptime(str(e) + '.00', "%H:%M:%S.%f")
                                    else:
                                        e = datetime.datetime.strptime(str(e), "%H:%M:%S.%f")
                                    file.write(datetime.datetime.strftime(s, '%H:%M:%S,%f')[:-3] + ' --> ' +
                                               datetime.datetime.strftime(e, '%H:%M:%S,%f')[:-3] + '\n')
                                for s in self.subs.split('\n\n')[i + self.starting_subtitle].split('\n')[2:]:
                                    sub += s + '\n'
                                len_words += len(sub.split())
                                file.write(sub)
                                file.write('\n')

                                #                 print(k, i)
                                if len_words > words_each_file or i == len(n_times) - 1:
                                    # print('yes', len_words, i)
                                    j += 1
                                    k = i + 1
                                    cut_list.append((start, i))
                                    #                 file.close()
                                    break

                            #         print('nnn', k)
                            if k == len(n_times):
                                run = False
                else:
                    j = 1
                    srt_file_name = self.save_location + '/' + str(j) + '--' + \
                                    self.file_name.split('/')[-1].split('.')[0] + '.srt'
                    with open(srt_file_name, 'w') as file:

                        #     for i in range(len(n_times)):
                        for i in range(len(n_times)):
                            sub = ''
                            file.write(str(i + 1) + '\n')
                            file.write(datetime.datetime.strftime(n_times[i][0], '%H:%M:%S,%f')[:-3] + ' --> ' +
                                       datetime.datetime.strftime(n_times[i][1], '%H:%M:%S,%f')[:-3] + '\n')
                            for s in self.subs.split('\n\n')[i + self.starting_subtitle].split('\n')[2:]:
                                sub += s + '\n'
                            file.write(sub)
                            file.write('\n')
                        cut_list.append((0, - 1 + self.ending_subtitle - self.starting_subtitle))
                self.ui.label_total_video.setText(str(len(cut_list)))
                self.ui.label_total_subs.setText(str(len(cut_list)))
                self.ui.label_target_res.setText(str(self.target_width) + '*' + str(self.targett_height))
                self.worker2 = ExtractClips(self.times, cut_list, self.video, self.forward, self.backward,
                                            self.gap, self.starting_subtitle, self.ending_subtitle)
                self.update_info('Subtitle is ready ... ' + '\n' + 'Start extracting ...', 1)

                self.worker2.signals.finished.connect(self.extract_cliped_finished)
                self.threadpool.start(self.worker2)

            except Exception as e:
                print('error', repr(e))
                self.update_info('Error extracting ...', 2)
                self.active = True
                self.ui.btn_run.setCursor(self.arrow_cursor)

        else:
            print('Wait to finish!')

    def extract_cliped_finished(self, status, video_clips):
        if status == 'ok':
            self.update_info('Finished extracting', 1)
            self.deliver_video(video_clips)
        else:
            self.active = True
            self.ui.btn_run.setCursor(self.arrow_cursor)
            self.update_info('Error extracting ...', 2)

    def load_video(self):
        if self.active:
            options = QFileDialog.Options()
            self.file_name, _ = QFileDialog.getOpenFileName(self, 'Open Video file', '',
                                                            "Videos (*.mp4 *.mkv *mov *avi *wmv)",
                                                            options=options)
            if self.file_name == '':
                return
            try:
                self.video = VideoFileClip(self.file_name)
                self.ui.label_video_name.setText(self.file_name.split('/')[-1])
                self.ui.label_video_duration.setText(
                    str(datetime.timedelta(seconds=self.video.duration)).split('.')[0])
                self.targett_width = self.video.size[0]
                self.targett_height = self.video.size[1]
                self.ui.label_video_resolution.setText(str(self.video.size[0]) + ' * ' + str(self.video.size[1]))
                self.ui.label_video_fps.setText(str(round(self.video.fps, 2)))
                self.ui.line_width.setText(str(self.video.size[0]))
                self.ui.line_height.setText(str(self.video.size[1]))
                self.update_info('Video is loaded !', 1)
            except Exception as e:
                print('loading video failed')
                print(repr(e))
        else:
            print('Wait to finish!')

    def load_subtitle(self):
        if self.active:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(self, 'Open Subtitle file', '',
                                                       "Subtitle (*.srt)",
                                                       options=options)
            if file_name != '':
                try:
                    lines = []

                    with open(file_name, 'r') as file:
                        for line in file:
                            lines.append(line)
                    self.times = []
                    self.subs = ''
                    for i, line in enumerate(lines):
                        self.subs += line
                        if ':' in line and '-->' in line:
                            time = line.split('-->')
                            try:
                                d1 = datetime.datetime.strptime(time[0].strip(), '%H:%M:%S,%f')
                            except Exception as e:
                                d1 = datetime.datetime.strptime(time[0].strip(), '%H:%M:%S')
                            try:
                                d2 = datetime.datetime.strptime(time[1].strip(), '%H:%M:%S,%f')
                            except Exception as e:
                                d2 = datetime.datetime.strptime(time[1].strip(), '%H:%M:%S')
                            self.times.append([d1, d2])
                    self.ui.label_subtitle_name.setText(file_name.split('/')[-1])
                    self.ui.label_subtitle_lines.setText(str(len(self.times)))
                    self.update_info('Subtitle is loaded !', 1)
                except Exception as e:
                    print('srt load error', repr(e))
        else:
            print('wait')


if __name__ == '__main__':
    app = QApplication([])
    window = MAINGUI()
    window.show()
    sys.exit(app.exec())
