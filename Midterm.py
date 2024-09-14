import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import random

# ตั้งกล่อง
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# เอารูปเข้า
imgBackground = cv2.imread("Resources/BGelden.jpg")
imgGameOver = cv2.imread("Resources/gameover.jpg")
imgWin = cv2.imread("Resources/win.jpg")  # ภาพที่จะแสดงเมื่อผู้เล่น 2 ชนะ
imgBall = cv2.imread("Resources/purple.png", cv2.IMREAD_UNCHANGED)
imgBat1 = cv2.imread("Resources/batgojo.png", cv2.IMREAD_UNCHANGED)
imgBat2 = cv2.imread("Resources/batskn.png", cv2.IMREAD_UNCHANGED)
imgKNIFE = cv2.imread("Resources/knife.png", cv2.IMREAD_UNCHANGED)

# ตัวตรวจจับมือ

detector = HandDetector(detectionCon=0.8, maxHands=1)

# ประกาศตัวแปรตอนเริ่มเกม
ballPos = [100, 100]
speedX = 15
speedY = 15
gameOver = False
hp = [10, 100]
width = 200
height = 20
hp_bars = []
min_speed = 5
max_speed = 100
bat_pos_left = (59, 0)  # ตำแหน่งของแป้นซ้ายเริ่มต้น
ballMoving = True  # ตัวแปรที่ใช้ตรวจสอบสถานะการเคลื่อนไหวของบอล
knife_list = []
knife_speed = 20
knife_width, knife_height = imgKNIFE.shape[:2]

# Function to spawn a new knife
def spawn_knife():
    knife_size = random.uniform(0.5, 1.5)  # สุ่มขนาดของมีด
    resized_knife = cv2.resize(imgKNIFE, (0, 0), fx=knife_size, fy=knife_size)
    knife_list.append([1280, random.randint(0, 720 - int(knife_height * knife_size)), resized_knife])
# Timer for knife spawning
knife_timer = 0
knife_spawn_interval = 0.25 # seconds


for i in range(11):  # 11 ภาพ ตั้งแต่ 0 ถึง 10
    hp_bars.append(cv2.imread(f"Resources/{i}Hpbar.png"))

# ฟังก์ชันสร้างบอลพร้อมขนาดสุ่ม
def create_ball(min_size, max_size):
    ball_scale = random.uniform(min_size, max_size)
    new_ball = cv2.resize(imgBall, (0, 0), fx=ball_scale, fy=ball_scale)
    return new_ball

# ฟังก์ชันสุ่มความเร็วบอล
def randomize_ball_speed():
    return random.randint(min_speed, max_speed), random.randint(min_speed, max_speed)

# ตั้งค่าเวลาเริ่มต้นสำหรับสุ่มขนาดบอลและความเร็วบอล
start_time_size = cv2.getTickCount()
start_time_speed = cv2.getTickCount()
ball_change_interval = 5  # หน่วยเป็นวินาที
imgBallResized = create_ball(0.5, 2)  # ขนาดบอลเริ่มต้น
speedX, speedY = randomize_ball_speed()

while True:
    _, img = cap.read()
    img = cv2.flip(img, 1)
    imgRaw = img.copy()

    # ตามหามือ
    hands, img = detector.findHands(img, flipType=False)

    # BACKGROUND
    img = cv2.addWeighted(img, 0, imgBackground, 0.8, 0)
    # Knife logic
    knife_timer += 1 / 60  # Assuming 60 FPS
    if knife_timer >= knife_spawn_interval:
        spawn_knife()
        knife_timer = 0

    for knife in knife_list:
        knife[0] -= knife_speed
        img = cvzone.overlayPNG(img, knife[2], knife)

        # ตรวจสอบการชนกับลูกบอล
        if ballPos[0] < knife[0] + knife[2].shape[1] and ballPos[0] + imgBallResized.shape[1] > knife[0] and \
           ballPos[1] < knife[1] + knife[2].shape[0] and ballPos[1] + imgBallResized.shape[0] > knife[1]:
            knife_list.remove(knife)  # ลบมีดออกจากรายการ

        # Check collision with left paddle
        if bat_pos_left[0] < knife[0] < bat_pos_left[0] + w1 and bat_pos_left[1] < knife[1] < bat_pos_left[1] + h1:
            hp[0] -= 1
            knife_list.remove(knife)  # Remove knife after collision
    # Remove knives that go off-screen
    knife_list = [knife for knife in knife_list if knife[0] > -knife_width]

    # เช็คมือ
    if hands:
        ballMoving = True  # บอลเคลื่อนไหวได้เมื่อพบมือ
        for hand in hands:
            x, y, w, h = hand['bbox']
            h1, w1, _ = imgBat1.shape
            x1 = x - w1 // 2
            y1 = y - h1 // 2
            x1 = np.clip(x1, 0, 1280 - w1)  # ตรวจสอบการขยับแป้นไม่ให้เกินขอบจอ
            y1 = np.clip(y1, 0, 720 - h1)  # ตรวจสอบการขยับแป้นไม่ให้เกินขอบจอ

            # วางแป้นสำหรับมือซ้าย
            if hand['type'] == "Right":
                img = cvzone.overlayPNG(img, imgBat1, (x1, y1))
                bat_pos_left = (x1, y1)  # อัปเดตตำแหน่งแป้นซ้าย

                # เช็คการชนกับลูกบอล
                if bat_pos_left[0] < ballPos[0] < bat_pos_left[0] + w1 and bat_pos_left[1] < ballPos[1] < bat_pos_left[1] + h1:
                    speedX = -speedX
                    speedY = random.randint(min_speed, max_speed)

    else:
        ballMoving = False  # บอลไม่เคลื่อนไหวเมื่อไม่พบมือ

    # เปลี่ยนขนาดบอลทุก 5 วินาที
    current_time_size = (cv2.getTickCount() - start_time_size) / cv2.getTickFrequency()
    if current_time_size > ball_change_interval:
        imgBallResized = create_ball(0.5, 2)  # สุ่มขนาดบอลใหม่
        start_time_size = cv2.getTickCount()  # รีเซ็ตเวลาเริ่มต้น

    # สุ่มความเร็วบอลทุก 5 วินาที
    current_time_speed = (cv2.getTickCount() - start_time_speed) / cv2.getTickFrequency()
    if current_time_speed > ball_change_interval:
        speedX, speedY = randomize_ball_speed()  # สุ่มความเร็วบอลใหม่
        start_time_speed = cv2.getTickCount()  # รีเซ็ตเวลาเริ่มต้น

    if ballPos[0] < -50 or ballPos[0] > 1330 or ballPos[1] < -50 or ballPos[1] > 770:
        if ballPos[0] < -50:
            hp[0] -= 1
        if ballPos[0] > 1330:
            hp[1] -= 1

        gameOver = hp[0] == 0 or hp[1] == 0
        if hp[0] != 0 or hp[1] != 0:
            # เพิ่มระยะห่างของตำแหน่งที่บอลจะเกิดใหม่จากแป้นซ้าย
            offset = 50  # ค่า offset ที่จะทำให้บอลเกิดห่างจากแป้นซ้าย
            ballPos = [bat_pos_left[0] + w1 // 2 + offset, bat_pos_left[1] - 10]  # วางบอลห่างจากแป้นซ้าย
            speedX, speedY = randomize_ball_speed()  # สุ่มความเร็วบอลใหม่
            imgBallResized = create_ball(0.5, 2)  # สุ่มขนาดบอลใหม่

    if hp[0] == 0:
        gameOver = True
        img = imgGameOver  # แสดงภาพ gameover
    elif hp[1] == 0:
        gameOver = True
        img = imgWin  # แสดงภาพ win
    else:
        # ตรวจสอบการชนกับขอบบนและขอบล่าง
        if ballPos[1] <= 0 or ballPos[1] >= 720 - imgBallResized.shape[0]:
            speedY = -speedY

        if ballMoving:  # เคลื่อนไหวบอลเมื่อ ballMoving เป็น True
            ballPos[0] += speedX
            ballPos[1] += speedY

        # วาดลูกบอล
        img = cvzone.overlayPNG(img, imgBallResized, ballPos)

        # HP BAR
        hp_bar_index = min(hp[0], 10)
        img[50:50 + hp_bars[hp_bar_index].shape[0], 100:100 + hp_bars[hp_bar_index].shape[1]] = hp_bars[hp_bar_index]

        hp_bar_index = min(max(hp[1] // 10, 0), 10)
        img[50:50 + hp_bars[hp_bar_index].shape[0], 900:900 + hp_bars[hp_bar_index].shape[1]] = hp_bars[hp_bar_index]

    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    if key == ord('r'):
        ballPos = [bat_pos_left[0] + w1 // 2, bat_pos_left[1] - 10]  # วางบอลที่แป้น
        speedX, speedY = randomize_ball_speed()
        gameOver = False
        hp = [10, 100]
        imgGameOver = cv2.imread("Resources/gameover.jpg")  # โหลดภาพ gameover ใหม่
        imgWin = cv2.imread("Resources/win.jpg")  # โหลดภาพ win ใหม่
