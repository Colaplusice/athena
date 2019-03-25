import cv2

video_catpure = cv2.VideoCapture(0)
video_catpure.set(3, 480)


while video_catpure.isOpened():
    ret, frame = video_catpure.read()
    cv2.imshow('video', frame)

video_catpure.release()
cv2.destroyAllWindows()
