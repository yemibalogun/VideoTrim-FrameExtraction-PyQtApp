---

# Desktop Application for Automated Video Frame Extraction

## Overview
This desktop application allows users to upload a folder containing multiple subfolders. Each subfolder should contain a video file (in .mp4 or .mov format). The application automatically processes each video to extract and save screenshots of the first and last frames as .jpg files within their respective subfolders.

## Features
- Upload a main folder containing subfolders with video files.
- Automatic detection of .mp4 and .mov files within subfolders.
- Extraction of the first and last frames of each video file.
- Saving of the extracted frames as .jpg images in the corresponding subfolders.
- Easy-to-use graphical user interface (GUI).

## System Requirements
- Operating System: Windows 10/11 or macOS 10.15 and above.
- Python 3.8 or higher.
- Required Libraries: `tkinter`, `opencv-python`, `PIL`, `os`, `shutil`.

## Installation
### For Windows:
1. Download the installer from [Link].
2. Run the installer and follow the on-screen instructions.
3. Once installed, launch the application from the desktop shortcut.

### For macOS:
1. Download the application package from [Link].
2. Open the downloaded package and move the application to the Applications folder.
3. Launch the application from the Applications folder.

### Using Python:
1. Clone the repository:
   ```
   git clone https://github.com/your-repo/video-frame-extraction.git
   ```
2. Navigate to the project directory:
   ```
   cd video-frame-extraction
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```

## Usage
### Step 1: Launch the Application
- Double-click the application icon to start the program.

### Step 2: Upload the Main Folder
- Click the "Upload Folder" button.
- Browse to select the main folder containing the subfolders with video files.
- The application will begin processing automatically.

### Step 3: Processing
- The application will process each video file in the subfolders:
  - Detects .mp4 and .mov files.
  - Extracts the first and last frames of each video.
  - Saves the extracted frames as `first_frame.jpg` and `last_frame.jpg` in each respective subfolder.

### Step 4: Completion
- A confirmation message will appear when processing is complete.
- You can now view the extracted frames in each subfolder.

## File Structure
```
Main Folder
│
├── Subfolder 1
│   ├── video.mp4
│   ├── first_frame.jpg
│   └── last_frame.jpg
│
├── Subfolder 2
│   ├── video.mov
│   ├── first_frame.jpg
│   └── last_frame.jpg
│
└── Subfolder n
    ├── video.mp4
    ├── first_frame.jpg
    └── last_frame.jpg
```

## Known Issues
- Video files with corrupt frames may not process correctly.
- Unsupported file formats will be skipped.

## Support
If you encounter any issues or have questions, please contact our support team at [yemibalogun2006@gmail.com].

---
