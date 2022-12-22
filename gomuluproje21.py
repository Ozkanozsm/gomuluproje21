# %%
import dlib 
import cv2
import numpy as np

from board import SCL, SDA
import busio
from oled_text import OledText
import RPi.GPIO as GPIO

GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def test_callback(channel):
    if(len(chars)>0):
        chars.pop()
        oled.text("".join(chars), 1)

def test_callback_2(channel):
    chars.append(" ")
    oled.text("".join(chars), 1)
    
GPIO.add_event_detect(21, GPIO.FALLING, callback=test_callback)
GPIO.add_event_detect(20, GPIO.FALLING, callback=test_callback_2)
i2c = busio.I2C(SCL, SDA)

# Create the display, pass its pixel dimensions
oled = OledText(i2c, 128, 64)
#oled.layout = Layout64.layout_1big_center()
oled.text("starting...", 3)
# Write to the oled

#oled.text("... world!", 2)  # Line 2
# %%

# %%
# Load the detector
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# %%
def calculate_distance(x1,y1, x2,y2):
    return np.sqrt((x2-x1)**2 + (y2-y1)**2)

# %%
def calculate_aspect_ratio(landmarks):
    x1, y1 = landmarks.part(36).x, landmarks.part(36).y
    x2, y2 = landmarks.part(39).x, landmarks.part(39).y
    left_eye_x = calculate_distance(x1, y1, x2, y2)
    x1, y1 = landmarks.part(42).x, landmarks.part(42).y
    x2, y2 = landmarks.part(45).x, landmarks.part(45).y
    right_eye_x = calculate_distance(x1, y1, x2, y2)

    left_eye_y = (calculate_distance(landmarks.part(37).x, landmarks.part(37).y, landmarks.part(41).x, landmarks.part(41).y) + calculate_distance(landmarks.part(38).x, landmarks.part(38).y, landmarks.part(40).x, landmarks.part(40).y)) / 2
    right_eye_y = (calculate_distance(landmarks.part(43).x, landmarks.part(43).y, landmarks.part(47).x, landmarks.part(47).y) + calculate_distance(landmarks.part(44).x, landmarks.part(44).y, landmarks.part(46).x, landmarks.part(46).y)) / 2
    
    left_eye_aspect_ratio = left_eye_x / left_eye_y
    right_eye_aspect_ratio = right_eye_x / right_eye_y

    return (left_eye_aspect_ratio + right_eye_aspect_ratio) / 2

# %%
# write mors code alphabet in array
morse_code = {
    "A": ".-", "B": "-...",
    "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....",
    "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--",
    "N": "-.", "O": "---", "P": ".--.",
    "Q": "--.-", "R": ".-.", "S": "...",
    "T": "-", "U": "..-", "V": "...-",
    "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
    "1": ".----", "2": "..---", "3": "...--",
    "4": "....-", "5": ".....", "6":
    "-....", "7": "--...", "8": "---..",
    "9": "----.", "0": "-----", " ": " "}


# %%
# create a VideoCapture object
cap = cv2.VideoCapture(0)
# set resolution
cap.set(3, 160)
cap.set(4, 120)


last_classifications = []
chars = []
written = []
oldwritten = []
oled.text("" ,3)
seenface = 1

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.resize(frame, (120, 90), interpolation=cv2.INTER_CUBIC)
    faces = detector(frame)
    
    for face in faces:
        if(seenface==0):
            seenface=1
            oled.text("detected face", 5)
        landmarks = predictor(frame, face)
        eye_aspect_ratio = calculate_aspect_ratio(landmarks)
        if eye_aspect_ratio > 5.1:
            last_classifications.append(1)
        else:
            last_classifications.append(0)
        if len(last_classifications) > 35:
            if sum(last_classifications[-6:]) == 0:
                last_sum = sum(last_classifications)
                if last_sum > 5:
                    chars.append("-")
                    oled.text("".join(chars), 1)
                elif last_sum > 2:
                    chars.append(".")
                    oled.text("".join(chars), 1)
                last_classifications = []
        # deep copy chars to tempchars
        tempchars = chars.copy()

        # add to written while all chars and add to written when space
        i = 0
        written = []
        while i < len(tempchars):
            if tempchars[i] == " ":
                thischar = "".join(tempchars[:i])
                i += 1
                for key, value in morse_code.items():
                    if (value == thischar):
                        # print(key)
                        written.append(key)
                        break
                tempchars = tempchars[i:]
                i = 0
                
            else:
                i += 1
        
        if(oldwritten!=written):
            oldwritten = written.copy()
            oled.text("".join(written), 3)  # Line 3
        
        
        #print("".join(written))
        #print(chars)
    if(not faces):
        if(seenface==1):
            seenface=0
            oled.text("no face detected", 5)
            
        # print written to frame
        """
        cv2.putText(frame, "".join(written), (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        
        for n in range(36, 48):
            x = landmarks.part(n).x
            y = landmarks.part(n).y
            
            cv2.circle(frame, (x, y), 1, (255, 0, 0), -1)
            # add n as text
            cv2.putText(frame, str(n), (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        """

    # Display the resulting frame
    # cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


