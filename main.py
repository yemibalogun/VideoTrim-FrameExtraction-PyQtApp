import sys
import os
import subprocess
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QFileDialog, QLineEdit, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class Worker(QThread):
    # Define signals to communicate with the main thread
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, companies_folder, trim_duration, ffmpeg_path):
        super().__init__()
        self.companies_folder = companies_folder
        self.trim_duration = trim_duration
        self.ffmpeg_path = ffmpeg_path

    def run(self):
        try:
            for subdir, _, files in os.walk(self.companies_folder):
                if subdir == self.companies_folder:
                    continue

                self.progress.emit(f"Processing folder: {subdir}")

                # Look for an mp4 or mov file
                video_files = [f for f in files if f.lower().endswith(('.mp4', '.mov'))]
                if not video_files:
                    self.progress.emit(f"No video file found in {subdir}")
                    continue

                original_video_path = os.path.join(subdir, video_files[0])
                trimmed_video_path = os.path.join(subdir, 'trimmed_video.mp4')

                # Trim the video
                try:
                    self.progress.emit(f"Trimming video: {original_video_path}")
                    subprocess.run([
                        self.ffmpeg_path, '-i', original_video_path, '-t', str(self.trim_duration),
                        '-c', 'copy', trimmed_video_path
                    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.progress.emit(f"Trimmed video to {self.trim_duration} seconds.")
                except subprocess.CalledProcessError as e:
                    self.progress.emit(f"Failed to trim video in {subdir}: {e.stderr.decode().strip()}")
                    continue

                # Replace the original video with the trimmed video
                try:
                    os.remove(original_video_path)
                    os.rename(trimmed_video_path, original_video_path)
                    self.progress.emit(f"Replaced original video with trimmed video in {subdir}.")
                except Exception as e:
                    self.progress.emit(f"Error replacing video in {subdir}: {e}")
                    continue

                # Convert the video to H.264 - MPEG-4 AVC codec
                converted_video_path = os.path.join(subdir, 'converted_video.mp4')
                try:
                    self.progress.emit(f"Converting video codec to H.264: {original_video_path}")
                    subprocess.run([
                        self.ffmpeg_path, '-i', original_video_path,
                        '-vcodec', 'libx264', '-acodec', 'aac', converted_video_path
                    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.progress.emit("Converted video to H.264 successfully.")

                    os.remove(original_video_path)
                    os.rename(converted_video_path, original_video_path)
                    self.progress.emit("Replaced original video with H.264 encoded video.")
                except subprocess.CalledProcessError as e:
                    self.progress.emit(f"Failed to convert video in {subdir} to H.264: {e.stderr.decode().strip()}")
                    continue

                # Extract first and last frames
                self.progress.emit(f"Extracting frames from video: {original_video_path}")
                cap = cv2.VideoCapture(original_video_path)
                if not cap.isOpened():
                    self.progress.emit(f"Error opening video file {original_video_path}")
                    continue

                # Read first frame
                ret, first_frame = cap.read()
                if ret:
                    first_frame_path = os.path.join(subdir, 'first_frame.jpg')
                    cv2.imwrite(first_frame_path, first_frame)
                    self.progress.emit(f"Saved first frame to {first_frame_path}")
                else:
                    self.progress.emit(f"Failed to read first frame from {original_video_path}")

                # Read last frame
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if total_frames > 0:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
                    ret, last_frame = cap.read()
                    if ret:
                        last_frame_path = os.path.join(subdir, 'last_frame.jpg')
                        cv2.imwrite(last_frame_path, last_frame)
                        self.progress.emit(f"Saved last frame to {last_frame_path}")
                    else:
                        self.progress.emit(f"Failed to read last frame from {original_video_path}")
                else:
                    self.progress.emit(f"No frames found in {original_video_path}")

                cap.release()

                # Resize PNG images
                png_files = [f for f in files if f.lower().endswith('.png')]
                if png_files:
                    png_path = os.path.join(subdir, png_files[0])
                    self.progress.emit(f"Resizing PNG image: {png_path}")
                    png_image = cv2.imread(png_path)
                    if png_image is not None:
                        resized_png = cv2.resize(png_image, (1920, 1080))
                        cv2.imwrite(png_path, resized_png)
                        self.progress.emit(f"Resized PNG image in {subdir} to 1920x1080.")
                    else:
                        self.progress.emit(f"Failed to load PNG image {png_path}")
                else:
                    self.progress.emit(f"No PNG file found in {subdir}")

            self.progress.emit("Processing complete.")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Companies Folder Processor")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Select folder button
        self.select_button = QPushButton("Select Companies Folder")
        self.select_button.clicked.connect(self.select_folder)
        layout.addWidget(self.select_button)

        # Display selected folder path
        self.folder_label = QLabel("No folder selected.")
        layout.addWidget(self.folder_label)

        # Trim duration input
        self.trim_label = QLabel("Trim Duration (seconds):")
        layout.addWidget(self.trim_label)
        self.trim_input = QLineEdit("5.96")
        layout.addWidget(self.trim_input)

        # Start processing button
        self.start_button = QPushButton("Start Processing")
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setEnabled(False)
        layout.addWidget(self.start_button)

        # Progress log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Companies Folder")
        if folder:
            self.folder_label.setText(folder)
            self.selected_folder = folder
            self.start_button.setEnabled(True)

    def start_processing(self):
        trim_duration_str = self.trim_input.text()
        try:
            trim_duration = float(trim_duration_str)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Trim duration must be a number.")
            return

        # Determine the base path (for PyInstaller)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        ffmpeg_path = os.path.join(base_path, 'bin', 'ffmpeg.exe')

        if not os.path.exists(ffmpeg_path):
            QMessageBox.critical(self, "FFmpeg Not Found", f"FFmpeg not found at {ffmpeg_path}. Please ensure FFmpeg is bundled with the application.")
            return

        # Disable buttons to prevent multiple processing
        self.start_button.setEnabled(False)
        self.select_button.setEnabled(False)
        self.log.append("Starting processing...")

        # Initialize and start the worker thread
        self.worker = Worker(self.selected_folder, trim_duration, ffmpeg_path)
        self.worker.progress.connect(self.update_log)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()

    def update_log(self, message):
        self.log.append(message)

    def handle_error(self, error_message):
        self.log.append(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)
        self.start_button.setEnabled(True)
        self.select_button.setEnabled(True)

    def processing_finished(self):
        self.log.append("All processing complete.")
        QMessageBox.information(self, "Completed", "All processing is complete.")
        self.start_button.setEnabled(True)
        self.select_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
