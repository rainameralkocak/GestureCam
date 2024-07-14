import cv2 
import mediapipe as mp 
import time 
import speech_recognition as sr 

mp_drawing = mp.solutions.drawing_utils 
mp_drawing_styles = mp.solutions.drawing_styles  
mp_hands = mp.solutions.hands 

cap = cv2.VideoCapture(0)
hand_closed = False 

previous_finger_count = 0
counter_start_time = time.time()
recorded_count = None 
geri_sayim = None
flash_opened = None 
exit_program = None

r = sr.Recognizer() 
mic = sr.Microphone() 

with mic as source: 
        print("Sesinizi bekliyorum...")
        r.adjust_for_ambient_noise(source)  

        audio = r.listen(source)  
        try:
            text = r.recognize_google(audio, language="tr-TR")  
            print(f"Ses algilandi: {text}")

            if "flaş aç" in text.lower():
                print("Flaş açildi!")
                flash_opened = True
                exit_program = False
            elif "flaş kapat" in text.lower():
                print("Flaş kapatildi!")
                flash_opened = False
                exit_program=False
            else: 
               print("TANIMLANMAYAN KOMUT!")
               exit_program = True   

        except sr.UnknownValueError:
            print("TANIMLANMAYAN KOMUT!")
            exit_program = True
        except sr.RequestError:
            print("Ses servisi çalişmiyor !")
            exit_program = True

with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as hands:
  while cap.isOpened() and (geri_sayim is None or geri_sayim >0) and exit_program == False:
    success, image = cap.read()
    if not success:
      print("Boş kamera görüntüsünü görmezden geliyor.")
      continue

    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image)

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    fingerCount = 0

    if results.multi_hand_landmarks:

      for hand_landmarks in results.multi_hand_landmarks:
        handIndex = results.multi_hand_landmarks.index(hand_landmarks)
        handLabel = results.multi_handedness[handIndex].classification[0].label

        handLandmarks = []

        for landmarks in hand_landmarks.landmark:
          handLandmarks.append([landmarks.x, landmarks.y])

        if handLabel == "Left" and handLandmarks[4][0] > handLandmarks[3][0]:
          fingerCount = fingerCount+1
        elif handLabel == "Right" and handLandmarks[4][0] < handLandmarks[3][0]:
          fingerCount = fingerCount+1

        if handLandmarks[8][1] < handLandmarks[6][1]:     
          fingerCount = fingerCount+1
        if handLandmarks[12][1] < handLandmarks[10][1]:    
          fingerCount = fingerCount+1
        if handLandmarks[16][1] < handLandmarks[14][1]:   
          fingerCount = fingerCount+1
        if handLandmarks[20][1] < handLandmarks[18][1]:    
          fingerCount = fingerCount+1

        mp_drawing.draw_landmarks(
            image,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())

      if fingerCount == 0: 
        hand_closed = True

    if hand_closed:
        cv2.putText(image, "El kapali, kamera kapatiliyor...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('MediaPipe Hands', image)
        cv2.waitKey(2000)  
        break

    if fingerCount != previous_finger_count:
        counter_start_time = time.time()
        previous_finger_count = fingerCount

    if fingerCount > 0:
       if time.time() - counter_start_time >=2 and fingerCount == previous_finger_count:
          recorded_count = fingerCount


    if recorded_count is not None and recorded_count >= 0 :
        if geri_sayim is None and time.time() - counter_start_time >= 3:
            geri_sayim = recorded_count

    if geri_sayim is not None:
        cv2.putText(image, f"Geri Sayim: {geri_sayim}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        if geri_sayim > 0:
            cv2.putText(image, f"Geri Sayim: {geri_sayim}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            if time.time() - counter_start_time >= 1:
                geri_sayim -= 1
                counter_start_time = time.time()  

            if geri_sayim == 0:
                success, frame = cap.read()
                if success:
                    if flash_opened == True:
                       cv2.imwrite("flashacikfoto.jpg", frame)
                       print("Fotoğraf flaş açıkken çekildi!")
                    else:
                       flash_opened == False
                       cv2.imwrite("flashkapalifoto.jpg", frame)  
                       print("Fotoğraf flaş kapalıyken çekildi!")
                    break

    cv2.putText(image, f"Parmak Sayisi: {fingerCount}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow('MediaPipe Hands', image)

    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()