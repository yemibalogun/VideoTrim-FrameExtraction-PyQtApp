import sys
import os
import subprocess
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QFileDialog, QLineEdit, QTextEdit, QMessageBox, QProgressBar
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer

class Worker(QThread):
    # Define signals to communicate with the main thread
    progress = pyqtSignal(str)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress_value = pyqtSignal(int)

    def __init__(self, companies_folder, trim_duration, ffmpeg_path):
        super().__init__()
        self.companies_folder = companies_folder
        self.trim_duration = trim_duration
        self.ffmpeg_path = ffmpeg_path

    def run(self):
        try:
            total_subfolders = sum([len(files) for _, _, files in os.walk(self.companies_folder) if files])
            current_folder = 0
            
            for subdir, _, files in os.walk(self.companies_folder):
                if subdir == self.companies_folder:
                    continue
                
                current_folder += 1
                progress_percent = int((current_folder / total_subfolders) * 100)
                self.progress_value.emit(progress_percent)
                self.progress.emit(f"Processing folder: {subdir}")
                
                # Look for video files
                video_files = [f for f in files if f.lower().endswith(('.mp4', '.mov'))]
                if not video_files:
                    self.progress.emit(f"No video files found in {subdir}")
                    continue
                for video_file in video_files:
                    original_video_path = os.path.join(subdir, video_file)
                    trimmed_video_path = os.path.join(subdir, f'trimmed_{video_file}')
                    self.trim_and_replace_video(original_video_path, trimmed_video_path, subdir)
                    
                self.progress_value.emit(100)
                self.progress.emit(f"Finished processing folder: {subdir}")
                
            self.progress.emit("Processing complete.")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def trim_and_replace_video(self, original_video_path, trimmed_video_path, subdir):
        # Trim the video using FFmpeg
        try:
            self.progress.emit(f"Trimming video: {original_video_path}")
            subprocess.run([
                self.ffmpeg_path, '-i', original_video_path, '-t', str(self.trim_duration),
                '-c', 'copy', trimmed_video_path
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.progress.emit(f"Trimmed video to {self.trim_duration} seconds.")

            # Replace the original video with the trimmed video
            os.remove(original_video_path)
            os.rename(trimmed_video_path, original_video_path)
            self.progress.emit(f"Replaced original video with trimmed video: {original_video_path}")

            # Extract first and last frames
            self.extract_frames(original_video_path, subdir, original_video_path)

        except subprocess.CalledProcessError as e:
            self.progress.emit(f"Failed to trim video {original_video_path}: {e.strderr.decode().strip()}")
        
    def extract_frames(self, video_path, subdir, original_video_path):
        self.progress.emit(f"Extracting frames from video: {video_path}")
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            self.progress.emit(f"Error opening video file {video_path}")
            return

        # Read first frame
        ret, first_frame = cap.read()
        if ret:
            first_frame_path = os.path.join(subdir, f"{os.path.splitext(os.path.basename(video_path))[0]}_first_frame.jpg")
            cv2.imwrite(first_frame_path, first_frame)
            self.progress.emit(f"Saved first frame to {first_frame_path}")
        else:
            self.progress.emit(f"Failed to read first frame from {video_path}")

        # Read last frame
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
            ret, last_frame = cap.read()
            if ret:
                last_frame_path = os.path.join(subdir, f"{os.path.splitext(os.path.basename(video_path))[0]}_last_frame.jpg")
                cv2.imwrite(last_frame_path, last_frame)
                self.progress.emit(f"Saved last frame to {last_frame_path}")
            else:
                self.progress.emit(f"Failed to read last frame from {video_path}")
        else:
            self.progress.emit(f"No frames found in {video_path}")

        cap.release()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BrandPeak1 Folder Processor")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon('./logobrandpeak.jpg'))
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout() # Initialize the layout first
        
        # Create and style the progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #5c5c5c;
                border-radius: 5px;
                background-color: #2e2e2e;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                width: 20px;
                margin: 1px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.setStyleSheet("""
                QWidget {
                    background-color: #2e2e2e;
                    color: #f0f0f0;
                    font-family: 'Roboto', sans-serif;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #3a3a3a;
                    border: 2px solid #5c5c5c;
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #505050;
                    border: 2px solid #707070;
                }
                QLabel {
                    color: #ffffff;
                    font-weight: bold;
                }
                QLineEdit {
                    background-color: #3a3a3a;
                    border: 2px solid #5c5c5c;
                    border-radius: 5px;
                    padding: 5px;
                    color: #ffffff;
                }
                QTextEdit {
                    background-color: #3a3a3a;
                    border: 2px solid #5c5c5c;
                    border-radius: 5px;
                    padding: 10px;
                    color: #ffffff;
                }
            """)
        
        # Select folder button
        self.select_button = QPushButton("Select Companies Folder...")
        self.select_button.setIcon(QIcon(''))
        self.select_button.clicked.connect(self.select_folder)
        layout.addWidget(self.select_button)

        # Display selected folder path
        self.folder_label = QLabel("No folder selected.")
        layout.addWidget(self.folder_label)

        # Trim duration input
        self.trim_label = QLabel("Trim Duration (seconds):")
        layout.addWidget(self.trim_label)
        self.trim_input = QLineEdit("6")
        self.trim_input.setPlaceholderText("Enter trim duration in seconds")
        layout.addWidget(self.trim_input)

        # Start processing button
        self.start_button = QPushButton("Start Processing")
        self.start_button.setToolTip("Click to start processing videos")
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
        self.worker.progress_value.connect(self.update_progress_bar)
        self.worker.progress.connect(self.update_log)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

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
