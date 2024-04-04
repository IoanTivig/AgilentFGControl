# ------------------------------------------------------
# ------------------ OpenDEP Control -------------------
# ------------------------------------------------------
import datetime
import time

from PyQt5.QtCore import QThread
# Standard imports #
from PyQt5.QtWidgets import QMainWindow, QDialog, QApplication
from PyQt5.uic import loadUi

# Local imports #
import src.classes.function_generator_control as func_gen

'''
AgilentFG Control
    Copyright (C) 2024  Ioan Cristian Tivig

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    You can contact the developer/owner of OpenDEP at "ioan.tivig@gmail.com".
'''


class MainUI(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("ui/main.ui", self)
        self.setWindowTitle("AgilentFG Control")
        # self.setWindowIcon(QIcon("icon.png"))

        self.generator = func_gen.FunctionGenerator()
        self.threads = []

        self.pyqt5_button_refresh_com.clicked.connect(self.refresh_coms_in_combobox)
        self.pyqt5_button_connect_com.clicked.connect(self.connect_to_selected_com)
        self.pyqt5_button_start.clicked.connect(self.threading_amplitude_ramping)
        self.pyqt5_button_stop.clicked.connect(self.thread_amplitude_ramping_stop)

    def refresh_coms_in_combobox(self):
        coms = self.generator.get_all_instruments()
        self.pyqt5_combobox_com.clear()
        self.pyqt5_combobox_com.addItems(coms)

    def connect_to_selected_com(self):
        try:
            selected_port = self.pyqt5_combobox_com.currentText()
            self.generator.connect_instrument(instrument_id=selected_port)
            print("Connected to", selected_port)
        except:
            print("Error connecting to instrument")

    def start_amplitude_ramping(self):
        frequency = self.pyqt5_entry_frequency.text()
        start_amplitude = float(self.pyqt5_entry_amplitude_start.text())
        stop_amplitude = float(self.pyqt5_entry_amplitude_stop.text())
        increment = float(self.pyqt5_entry_amplitude_increment.text())
        time_interval = self.pyqt5_entry_time_increment.text()

        total_time = 0
        self.generator.set_frequency(frequency)


        for amplitude in self.float_range(start_amplitude, stop_amplitude, increment):
            self.generator.set_voltage(amplitude)
            self.generator.start_output()

            # Get the current time
            start_time = datetime.datetime.now()

            # Calculate the end time
            end_time = start_time + datetime.timedelta(seconds=int(time_interval))

            # Set total time spent
            total_time += int(time_interval)
            self.pyqt5_dinamiclabel_countdown_total.setText(str(total_time))

            # Wait until the current time is equal to the end time
            while datetime.datetime.now() < end_time:
                time.sleep(0.01)  # Sleep for a short amount of time to prevent high CPU usage
                self.pyqt5_dinamiclabel_countdown_increment.setText(str((end_time - datetime.datetime.now()).seconds)) # Update the countdown label

        self.generator.stop_output()

    def float_range(self, start, stop, step):
        while start < stop:
            yield round(start, 10)  # rounding to avoid floating-point arithmetic issues
            start += step

    def threading_amplitude_ramping(self):
        self.threads.append(QThread())
        self.thread_amplitude_ramping = self.threads[-1]
        self.worker_amplitude_ramping = GeneratorRampingWorker(main_ui=self)
        self.worker_amplitude_ramping.moveToThread(self.thread_amplitude_ramping)
        self.thread_amplitude_ramping.started.connect(self.worker_amplitude_ramping.run)
        self.worker_amplitude_ramping.finished.connect(self.thread_amplitude_ramping.quit)
        self.worker_amplitude_ramping.finished.connect(self.worker_amplitude_ramping.deleteLater)
        self.thread_amplitude_ramping.finished.connect(self.thread_amplitude_ramping.deleteLater)
        self.thread_amplitude_ramping.start()

    def thread_amplitude_ramping_stop(self):
        self.worker_amplitude_ramping.stop()


class GeneratorRampingWorker(QThread):
    def __init__(self, main_ui):
        QThread.__init__(self)
        self.main_ui = main_ui
        self.generator = main_ui.generator
        self.is_running = True

    def run(self):
        frequency = self.main_ui.pyqt5_entry_frequency.text()
        start_amplitude = float(self.main_ui.pyqt5_entry_amplitude_start.text())
        stop_amplitude = float(self.main_ui.pyqt5_entry_amplitude_stop.text())
        increment = float(self.main_ui.pyqt5_entry_amplitude_increment.text())
        time_interval = self.main_ui.pyqt5_entry_time_increment.text()

        # Start a countdown timer until the start of the amplitude ramping
        for i in range(int(self.main_ui.pyqt5_entry_countdown.text()), 0, -1):
            if not self.is_running:
                break

            self.main_ui.pyqt5_dinamiclabel_countdown_increment.setText("Experiment starts in: " + str(i))
            time.sleep(1)

        total_start_time = datetime.datetime.now()
        self.generator.set_frequency(frequency)

        for amplitude in self.main_ui.float_range(start_amplitude, stop_amplitude+increment, increment):
            if not self.is_running:
                break

            self.generator.set_voltage(amplitude)
            self.main_ui.pyqt5_dinamiclabel_amplitude_current.setText(str(amplitude))
            self.generator.start_output()

            # Get the current time
            start_time = datetime.datetime.now()

            # Calculate the end time
            end_time = start_time + datetime.timedelta(seconds=int(time_interval))

            # Wait until the current time is equal to the end time
            while datetime.datetime.now() < end_time:
                time.sleep(0.01)  # Sleep for a short amount of time to prevent high CPU usage
                increment_time_passed = datetime.datetime.now() - start_time
                increment_time_passed = str(increment_time_passed).split(".")[0]
                self.main_ui.pyqt5_dinamiclabel_countdown_increment.setText(increment_time_passed)

                total_passed_time = datetime.datetime.now() - total_start_time
                total_passed_time = str(total_passed_time).split(".")[0]
                self.main_ui.pyqt5_dynamiclabel_total_time.setText(str(total_passed_time))

        self.generator.stop_output()

    def stop(self):
        self.is_running = False