import pygame
import random
import sys
import os  # 추가: 이미지 경로 설정을 위해 os 모듈 사용

# 초기화
pygame.init()

# 화면 크기 설정
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("소행성 충돌")  # 제목 수정

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# 폰트 설정 (한글 폰트 경로 지정)
font_path = "C:/Windows/Fonts/malgun.ttf"  # Windows의 '맑은 고딕' 폰트 경로
font = pygame.font.Font(font_path, 30)

# 이미지 로드
try:
    meteorite_image = pygame.image.load(os.path.join("assets", "meteorite.png")).convert_alpha()
    spaceship_image = pygame.image.load(os.path.join("assets", "spaceship.png")).convert_alpha()
    enemy_spaceship_image = pygame.image.load(os.path.join("assets", "enemy_spaceship.png")).convert_alpha()
except Exception as e:
    print(f"이미지 로드 실패: {e}")
    meteorite_image = spaceship_image = enemy_spaceship_image = None

# 보스 이미지 로드
try:
    boss_image = pygame.image.load(os.path.join("assets", "boss.png")).convert_alpha()
except Exception as e:
    print(f"보스 이미지 로드 실패: {e}")
    boss_image = None

# 총알 이미지 로드
try:
    bullet_image = pygame.image.load(os.path.join("assets", "bullet.png")).convert_alpha()
except Exception as e:
    print(f"총알 이미지 로드 실패: {e}")
    bullet_image = None

# 게임 변수 초기화
clock = pygame.time.Clock()
score = 0
speed = 5
comets = []
enemies = []  # 적 리스트 초기화
player_size = 50  # player_size 초기화
player_pos = [WIDTH // 2, HEIGHT - 2 * player_size]

# 아이템 이미지 로드 (player_size 초기화 이후)
item_images = {}
item_types = [
    "score_boost", "shield", "destroy_comets", "slow_down", "double_score",
    "invisibility", "shrink", "double_bullet", "fast_bullet", "strong_bullet",
    "speed_boost", "freeze_comets", "extra_life", "explosion"
]
for item_type in item_types:
    try:
        # 이미지 로드 후 크기를 50x50으로 조정
        original_image = pygame.image.load(os.path.join("assets", f"{item_type}.png")).convert_alpha()
        item_images[item_type] = pygame.transform.scale(original_image, (50, 50))
    except Exception as e:
        print(f"아이템 이미지 로드 실패 ({item_type}): {e}")
        # 기본 색상으로 대체
        item_images[item_type] = pygame.Surface((50, 50))
        item_images[item_type].fill((255, 0, 0))  # 빨간색으로 기본 처리

# 보호막 상태
shield_active = False

# 투명화 상태
invisibility_active = False
invisibility_timer = 0
player_alpha = 255  # 투명화 상태에서 사용할 알파값 초기화

# 아이템 관련 변수
selected_slot = 0  # 현재 선택된 슬롯
item_slots = [None, None, None]  # 아이템 슬롯 (최대 3개)

# 축소 상태
shrink_active = False
shrink_timer = 0

# 메시지 상태
message = ""
message_timer = 0

# 총알 상태
bullets = []
bullet_speed = 10
bullet_damage = 1
bullet_count = 1  # 기본 총알 개수 (1개)

# 기타 상태
freeze_timer = 0  # 시간 정지 타이머 초기화

# 무적 상태 변수 추가
invincible = False
invincible_timer = 0

# 하트 상태 추가
hearts = 3  # 최대 3개

# 총알 발사 속도 및 대미지 초기화
bullet_fire_interval = 5  # 기본 5초에 1발
bullet_damage = 100  # 기본 대미지
last_bullet_time = 0  # 마지막 총알 발사 시간

# 총알 충전 상태 변수 추가
bullet_charge = 0  # 현재 충전 상태 (0~100)
bullet_charge_rate = 100 / bullet_fire_interval  # 충전 속도 (초당 증가량)

# 소행성 생성 함수
def create_comet():
    while True:
        if meteorite_image:
            width = height = player_size  # 소행성 크기를 우주선 크기와 동일하게 설정
        else:
            width = height = random.randint(10, player_size)  # 기본 크기 축소
        x_pos = random.randint(0, WIDTH - width)
        y_pos = random.randint(-100, -50)  # 화면 위에서 랜덤 위치
        new_comet = {"pos": [x_pos, y_pos], "size": (width, height), "direction": "down"}
        # 기존 소행성과 겹치지 않으면 생성
        if not any(check_collision(new_comet, comet) for comet in comets):
            return new_comet

# 충돌 체크 함수
def check_collision(obj1, obj2):
    x1, y1 = obj1["pos"]
    w1, h1 = obj1["size"]
    x2, y2 = obj2["pos"]
    w2, h2 = obj2["size"]
    return (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2)

# 적 생성 함수
def create_enemy():
    size = enemy_spaceship_image.get_width() if enemy_spaceship_image else 40
    size = min(size, WIDTH)  # 적 크기를 화면 너비보다 작게 제한
    x_pos = random.randint(0, max(0, WIDTH - size))  # x_pos 범위가 음수가 되지 않도록 보정
    y_pos = random.randint(-100, -50)  # 화면 위에서 랜덤 위치
    return {"pos": [x_pos, y_pos], "size": size, "speed": 3}

# 적 제거 시 점수 보너스
def remove_enemy(enemy):
    global score
    enemies.remove(enemy)
    score += 100  # 적 제거 시 추가 점수

# 축소 효과 함수 (지속시간 10초로 변경 및 크기 반영)
def activate_shrink():
    global shrink_active, shrink_timer, player_size
    shrink_active = True
    shrink_timer = 10  # 10초 동안 지속
    player_size //= 2  # 우주선 크기 1/2로 축소

# 아이템 슬롯 정리 함수 (사용 후 슬롯 이동)
def shift_item_slots():
    global item_slots
    item_slots = [slot for slot in item_slots if slot is not None]  # None 제거
    while len(item_slots) < 3:  # 슬롯 개수 유지
        item_slots.append(None)

# 새로운 아이템 효과 함수 (하트 회복 및 기타 효과)
def apply_item_effect(item_type):
    global score, shield_active, comets, speed, score_increment, shrink_active, bullet_count, bullet_speed, bullets, freeze_timer, player_speed, invisibility_active, invisibility_timer, player_size, hearts, bullet_fire_interval, bullet_damage
    if item_type == "extra_life":
        if hearts < 3:  # 최대 3개까지 하트 추가
            hearts += 1
            show_message("하트가 추가되었습니다!")
        else:
            show_message("하트가 이미 최대치입니다!")
    elif item_type == "destroy_comets":
        comets.clear()  # 화면의 모든 소행성 제거
        show_message("소행성이 모두 제거되었습니다!")
    elif item_type == "explosion":
        if boss:  # 보스가 있을 경우
            boss = None
            show_message("보스가 제거되었습니다!")
        else:
            show_message("보스가 없습니다!")
    elif item_type == "score_boost":
        score += 50  # 점수 50 증가
        show_message("점수가 50 증가했습니다!")
    elif item_type == "shield":
        shield_active = True  # 보호막 활성화
        show_message("보호막이 활성화되었습니다!")
    elif item_type == "destroy_comets":
        comets.clear()  # 화면의 모든 소행성 제거
        show_message("소행성이 모두 제거되었습니다!")
    elif item_type == "slow_down":
        speed = max(speed - 2, 1)  # 소행성 속도 감소 (최소 1)
        show_message("소행성 속도가 느려졌습니다!")
    elif item_type == "double_score":
        score_increment *= 2  # 점수 증가 속도 2배
        show_message("점수 증가 속도가 2배로 증가했습니다!")
    elif item_type == "invisibility":
        invisibility_active = True  # 투명화 활성화
        invisibility_timer = 5  # 5초 동안 지속
        show_message("투명화가 활성화되었습니다!")
    elif item_type == "shrink":
        if not shrink_active:
            shrink_active = True
            shrink_timer = 10  # 10초 동안 지속
            player_size //= 2  # 플레이어 크기 절반으로 축소
        show_message("우주선 크기가 작아졌습니다!")
    elif item_type == "double_bullet":
        bullet_count = min(bullet_count + 1, 3)  # 총알 개수 최대 3발까지 증가
        show_message("총알 개수가 증가했습니다!")
    elif item_type == "fast_bullet":
        if bullet_fire_interval > 0.5:  # 최소 0.5초까지 발사 속도 증가
            bullet_fire_interval -= 1
            show_message("총알 발사 속도가 증가했습니다!")
        else:
            show_message("총알 발사 속도가 이미 최대치입니다!")
    elif item_type == "strong_bullet":
        if bullet_damage < 250:  # 최대 대미지 250까지 증가
            bullet_damage += 50
            show_message("총알 대미지가 증가했습니다!")
        else:
            show_message("총알 대미지가 이미 최대치입니다!")
    elif item_type == "speed_boost":
        player_speed += 2  # 플레이어 이동 속도 증가
        show_message("이동 속도가 증가했습니다!")
    elif item_type == "freeze_comets":
        freeze_timer = 5  # 소행성 정지 5초 동안 지속
        show_message("소행성이 멈췄습니다!")
    elif item_type == "extra_life":
        if hearts < 3:  # 최대 3개까지 하트 추가
            hearts += 1
            show_message("하트가 추가되었습니다!")
        else:
            show_message("하트가 이미 최대치입니다!")
    elif item_type == "explosion":
        comets.clear()  # 화면의 모든 소행성 제거
        show_message("모든 소행성이 제거되었습니다!")
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000)  # 1초 후 소행성 재생성

    # 아이템 사용 후 슬롯 이동
    shift_item_slots()

# 아이템 생성 함수 (아이템 크기 조정)
def create_item():
    size = (player_size, player_size)  # 아이템 크기를 우주선 크기와 동일하게 설정
    x_pos = random.randint(0, WIDTH - size[0])
    y_pos = random.randint(-100, -50)  # 화면 위에서 랜덤 위치
    item_type = random.choice(item_types)  # 아이템 타입 랜덤 선택
    return {"pos": [x_pos, y_pos], "size": size, "type": item_type}

# 최종 보스 생성 함수
def create_boss():
    width = WIDTH  # 보스 가로 크기: 화면 전체 너비
    height = int(HEIGHT * 0.2)  # 보스 세로 크기: 화면 높이의 20%
    x_pos = 0  # 화면 왼쪽부터 시작
    y_pos = 0  # 화면 위쪽에 고정
    health = 25000  # 보스 체력
    return {"pos": [x_pos, y_pos], "size": (width, height), "health": health, "speed": 0}  # speed는 0으로 설정

# 최종 보스 소행성 생성 함수
def create_boss_comet():
    size = 10  # 소행성 크기 (10x10)
    x_pos = random.randint(0, WIDTH - size)
    y_pos = random.randint(-100, -50)  # 화면 위에서 랜덤 위치
    health = 5  # 소행성 체력 (5번 공격받으면 파괴)
    return {"pos": [x_pos, y_pos], "size": size, "health": health}

# 투명화 효과 함수
def activate_invisibility():
    global invisibility_active, invisibility_timer
    invisibility_active = True
    invisibility_timer = 5  # 5초 동안 지속

# 점진적인 속도 증가 함수
def gradual_speed_increase(base_speed, elapsed_time):
    return base_speed + (elapsed_time // 30) * 0.1  # 30초마다 0.1씩 증가

# 메시지 표시 함수
def show_message(text, duration=1):
    global message, message_timer
    message = text
    message_timer = duration  # 메시지 표시 시간 (초)

# 총알 발사 함수 (총알 갯수 증가 반영)
def fire_bullet():
    global bullets, last_bullet_time, bullet_charge
    current_time = pygame.time.get_ticks() / 1000  # 현재 시간 (초 단위)
    if bullet_charge >= 100:  # 충전이 완료되었을 때만 발사
        bullet_charge = 0  # 충전 상태 초기화
        last_bullet_time = current_time
        for i in range(bullet_count):  # 총알 갯수만큼 발사
            offset = (i - bullet_count // 2) * 10  # 총알 간격 조정
            bullet_x = player_pos[0] + player_size // 2 - 5 + offset
            bullet_y = player_pos[1]
            bullets.append({"pos": [bullet_x, bullet_y], "damage": bullet_damage})

# 라운드별 패턴 설정 함수
def apply_round_pattern(round_number):
    global speed, comets, enemies, items
    if round_number == 1:
        speed = 5
    elif round_number == 2:
        speed = 6
        for _ in range(2):  # 적 추가
            enemies.append(create_enemy())
    elif round_number == 3:
        speed = 7
        for _ in range(3):  # 소행성 추가
            comets.append(create_comet())
    elif round_number == 4:
        speed = 8
        for _ in range(2):  # 아이템 추가
            items.append(create_item())
    elif round_number == 5:
        speed = 9
        for _ in range(4):  # 소행성과 적 추가
            comets.append(create_comet())
            enemies.append(create_enemy())
    elif round_number == 6:
        speed = 10
        for _ in range(5):  # 소행성 추가
            comets.append(create_comet())
    elif round_number == 7:
        speed = 11
        for _ in range(3):  # 적 추가
            enemies.append(create_enemy())
    elif round_number == 8:
        speed = 12
        for _ in range(6):  # 소행성 추가
            comets.append(create_comet())
    elif round_number == 9:
        speed = 13
        for _ in range(8):  # 소행성과 적 추가
            comets.append(create_comet())
            enemies.append(create_enemy())
    elif round_number % 3 == 0:  # 새로운 이벤트: meteor_shower
        for _ in range(10):  # 대량의 소행성 생성
            comets.append(create_comet())
        show_message("운석 폭풍이 시작됩니다!")
    elif round_number % 5 == 0:  # 새로운 이벤트: enemy_wave
        for _ in range(10):  # 대량의 적 생성
            enemies.append(create_enemy())
        show_message("적의 대규모 공격이 시작됩니다!")

# 라운드 계산 함수
def calculate_round(score):
    if score < 200:
        return 1
    elif score < 500:
        return 2
    elif score < 800:
        return 3
    elif score < 1200:
        return 4
    elif score < 1600:
        return 5
    elif score < 2100:
        return 6
    elif score < 2700:
        return 7
    elif score < 3500:
        return 8
    else:
        return 9

# 난이도 증가 함수 정의
def increase_difficulty(round_number):
    global speed, bullet_speed, enemies, comets
    speed = 5 + round_number  # 소행성 속도 증가
    bullet_speed = 10 + round_number  # 총알 속도 증가
    for _ in range(round_number):  # 라운드에 따라 적 추가
        enemies.append(create_enemy())
    for _ in range(round_number):  # 라운드에 따라 소행성 추가
        comets.append(create_comet())

# 하트 그리기 함수
def draw_hearts():
    for i in range(hearts):
        heart_x = 10 + i * 30  # 하트 간격
        heart_y = 50
        pygame.draw.circle(screen, RED, (heart_x, heart_y), 10)  # 하트는 빨간색 원으로 표시

# 총알 충전 상태 그리기 함수
def draw_bullet_charge():
    box_width, box_height = 20, 10  # 네모 박스 크기 (2x1 비율)
    spacing = 5  # 박스 간 간격
    start_x = WIDTH - 100  # 오른쪽 하단 시작 위치
    start_y = HEIGHT - 50

    # 총알 충전 상태에 따라 박스 색상 결정
    for i in range(3):
        if bullet_charge >= (i + 1) * 33.33:  # 충전 상태에 따라 박스 채우기
            color = (0, 255, 0)  # 초록색 (충전 완료)
        else:
            color = (50, 50, 50)  # 회색 (충전 중)
        pygame.draw.rect(screen, color, (start_x + i * (box_width + spacing), start_y, box_width, box_height))

# 메인 루프
while True:
    # 게임 변수 초기화 (초기 실행 시에만 초기화)
    if 'initialized' not in locals():
        initialized = True
        score = 0
        speed = 5
        score_increment = 1  # 점수 증가 속도
        score_timer = 0  # 점수 증가 타이머
        time_elapsed = 0  # 경과 시간
        round_number = 1  # 라운드 번호
        comets = []
        boss_comets = []  # 보스가 발사한 소행성 리스트
        enemies = []  # 적 리스트
        items = []  # 아이템 리스트
        boss = None  # 최종 보스
        player_pos = [WIDTH // 2, HEIGHT - 2 * player_size]
        item_slots = [None, None, None]  # 아이템 슬롯 초기화

    # 게임 루프
    running = True
    while running:
        screen.fill(BLACK)

        # 시간 계산
        delta_time = clock.get_time() / 1000  # 프레임 간 경과 시간
        time_elapsed += delta_time
        score_timer += delta_time

        # 투명화 상태 처리 (아이템 효과 반영)
        if invisibility_active:
            invisibility_timer -= delta_time
            if invisibility_timer <= 0:
                invisibility_active = False  # 투명화 종료
            elif invisibility_timer <= 1:  # 마지막 1초 동안 깜빡임 효과
                if int(invisibility_timer * 10) % 2 == 0:
                    player_alpha = 50  # 흐릿해짐
                else:
                    player_alpha = 255  # 선명해짐
            else:
                player_alpha = 100  # 흐릿한 상태 유지
        else:
            player_alpha = 255  # 기본 상태

        # 축소 상태 처리 (아이템 효과 반영)
        if shrink_active:
            shrink_timer -= delta_time
            if shrink_timer <= 1 and shrink_timer > 0:  # 지속시간 1초 전 경고 메시지
                show_message("우주선이 곧 있으면 원 상태로 돌아갑니다.")
            if shrink_timer <= 0:
                shrink_active = False  # 축소 종료
                player_size *= 2  # 우주선 크기 원래대로 복원

        # 메시지 타이머 처리
        if message_timer > 0:
            message_timer -= delta_time
            if message_timer <= 0:
                message = ""  # 메시지 초기화

        # 보호막 상태 처리
        if shield_active:
            pygame.draw.circle(screen, (255, 255, 0), (player_pos[0] + player_size // 2, player_pos[1] + player_size // 2), player_size, 3)  # 노란색 원

        # 점수 증가
        if score_timer >= 0.1:  # 점수 증가 속도를 더 빠르게 조정
            score += score_increment
            score_timer = 0

        # 라운드 계산 및 난이도 증가 (3초 무적 추가)
        new_round = calculate_round(score)
        if new_round > round_number:  # 라운드가 변경되었을 때만 난이도 증가
            round_number = new_round
            # 화면 검게 만들고 "다음 라운드 진입" 메시지 표시
            screen.fill(BLACK)
            next_round_text = font.render("다음 라운드 진입", True, WHITE)
            screen.blit(next_round_text, (WIDTH // 2 - next_round_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()  # 화면 업데이트
            pygame.time.wait(1000)  # 1초 대기 후 다음 라운드 시작

            # 3초 무적 상태 활성화
            invincible = True
            invincible_timer = 3  # 3초 동안 지속

            increase_difficulty(round_number)  # 난이도 증가
            show_message(f"라운드 {round_number} 시작!")  # 라운드 변경 메시지

        # 보스 등장 조건
        if score >= 1000 and boss is None:
            boss = create_boss()  # 보스 생성
            show_message("보스가 나타났습니다!")

        # 이벤트 처리 (아이템 사용 시 슬롯 이동 추가)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.USEREVENT + 1:  # explosion 아이템으로 소행성 다시 생성
                for _ in range(random.randint(3, 5)):  # 3~5개의 소행성 생성
                    comets.append(create_comet())
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # 타이머 해제
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # 스페이스바로 총알 발사
                    fire_bullet()
                elif event.key == pygame.K_RETURN:  # 엔터 키로 아이템 사용
                    if item_slots[selected_slot]:
                        apply_item_effect(item_slots[selected_slot])  # 아이템 효과 적용
                        item_slots[selected_slot] = None  # 사용 후 슬롯 비우기
                        shift_item_slots()  # 슬롯 이동
                elif event.key == pygame.K_1:  # 숫자 1로 첫 번째 슬롯 선택
                    selected_slot = 0
                elif event.key == pygame.K_2:  # 숫자 2로 두 번째 슬롯 선택
                    selected_slot = 1
                elif event.key == pygame.K_3:  # 숫자 3로 세 번째 슬롯 선택
                    selected_slot = 2

        # 플레이어 이동 (속도 증가 적용)
        keys = pygame.key.get_pressed()
        player_speed = 10  # 기본 이동 속도
        if keys[pygame.K_LEFT] and player_pos[0] > 0:  # 왼쪽 이동
            player_pos[0] -= player_speed
        if keys[pygame.K_RIGHT] and player_pos[0] < WIDTH - player_size:  # 오른쪽 이동
            player_pos[0] += player_speed
        if keys[pygame.K_UP] and player_pos[1] > 0:  # 위로 이동
            player_pos[1] -= player_speed
        if keys[pygame.K_DOWN] and player_pos[1] < HEIGHT - player_size:  # 아래로 이동
            player_pos[1] += player_speed

        # 소행성 생성 및 이동 (운석 개수 제한: 최대 3개)
        if len(comets) < 3 and random.randint(1, 20) == 1:  # 운석 생성 확률 조정 (1/20)
            comets.append(create_comet())  # 운석 생성 후 comets 리스트에 추가

        for comet in comets[:]:
            comet["pos"][1] += speed  # 소행성은 아래로만 이동
            if comet["pos"][1] > HEIGHT:
                comets.remove(comet)  # 화면 밖으로 나간 소행성 제거

            # 충돌 체크 (소행성과 플레이어만 체크)
            player_rect = {"pos": player_pos, "size": (player_size, player_size)}
            # 무적 상태 처리
            if invincible:
                invincible_timer -= delta_time
                if invincible_timer <= 0:
                    invincible = False  # 무적 상태 종료

            # 소행성 충돌 체크 (무적 상태 반영)
            if check_collision(player_rect, comet):
                if invincible or invisibility_active:
                    continue  # 무적 상태 또는 투명화 상태에서는 충돌 무시
                if shield_active:  # 보호막이 활성화된 경우
                    shield_active = False  # 보호막 비활성화
                    show_message("보호막이 깨졌습니다!")
                    comets.remove(comet)  # 소행성 제거
                else:
                    hearts -= 1  # 하트 소모
                    comets.remove(comet)  # 소행성 제거
                    if hearts <= 0:  # 하트가 모두 소모되면 게임 오버
                        running = False

        # 소행성 그리기
        for comet in comets:
            if meteorite_image:
                scaled_meteorite = pygame.transform.scale(meteorite_image, comet["size"])  # 크기 조정
                screen.blit(scaled_meteorite, comet["pos"])
            else:
                pygame.draw.rect(screen, RED, (*comet["pos"], *comet["size"]))  # 기본 사각형으로 그리기

        # 소행성 생성 및 이동 (8라운드부터 총 사용 필수)
        if round_number < 8:
            if random.randint(1, 15) == 1:  # 소행성 출현 확률
                comets.append(create_comet())
        elif round_number >= 8 and len(comets) == 0:  # 8라운드 이상에서는 총을 써야 소행성 제거 가능
            for _ in range(random.randint(3, 5)):  # 더 많은 소행성 생성
                comets.append(create_comet())

        # 소행성 생성 및 이동
        for comet in comets[:]:
            comet["pos"][1] += speed  # 소행성은 아래로만 이동
            if comet["pos"][1] > HEIGHT:
                comets.remove(comet)  # 화면 밖으로 나간 소행성 제거

            # 충돌 체크 (소행성과 플레이어만 체크)
            player_rect = {"pos": player_pos, "size": (player_size, player_size)}
            if check_collision(player_rect, comet):  # player_pos를 딕셔너리로 변환
                if shield_active:  # 보호막이 활성화된 경우
                    shield_active = False  # 보호막 비활성화
                    show_message("보호막이 깨졌습니다.")  # 보호막 깨짐 메시지
                    comets.remove(comet)  # 소행성 제거
                else:
                    # 게임 오버 메시지 표시
                    game_over_text = font.render("Game Over", True, RED)
                    screen.blit(game_over_text, (WIDTH // 2 - 100, HEIGHT // 2))
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    running = False

        # 적 생성 및 이동 (게임 오버 제거)
        if score >= 100 and random.randint(1, 30) == 1:  # 적 출현 확률
            enemies.append(create_enemy())
        for enemy in enemies[:]:
            enemy["pos"][1] += enemy["speed"]  # 적은 아래로 이동
            if enemy["pos"][1] > HEIGHT:
                enemies.remove(enemy)  # 화면 밖으로 나간 적 제거

            # 충돌 체크 (적과 플레이어 충돌 시 게임 오버 제거)
            player_rect = {"pos": player_pos, "size": (player_size, player_size)}
            enemy_rect = {"pos": enemy["pos"], "size": (enemy["size"], enemy["size"])}  # 적 크기를 (width, height)로 변환
            if check_collision(player_rect, enemy_rect):  # 충돌 체크
                if shield_active:  # 보호막이 활성화된 경우
                    shield_active = False  # 보호막 비활성화
                    enemies.remove(enemy)  # 적 제거
                else:
                    enemies.remove(enemy)  # 보호막이 없으면 적만 제거

        # 아이템 생성 및 이동 (스코어 100 이상부터, 5초에 1~2개 생성)
        if score >= 100 and random.randint(1, 150) == 1:  # 아이템 출현 확률 감소
            items.append(create_item())
        for item in items[:]:
            item["pos"][1] += 3  # 아이템은 천천히 아래로 이동
            if item["pos"][1] > HEIGHT:
                items.remove(item)  # 화면 밖으로 나간 아이템 제거

            # 아이템 획득 체크
            player_rect = {"pos": player_pos, "size": (player_size, player_size)}
            if check_collision(player_rect, item):  # player_pos를 딕셔너리로 변환
                # 빈 슬롯에 아이템 저장
                for i in range(3):
                    if item_slots[i] is None:
                        item_slots[i] = item["type"]
                        break
                items.remove(item)

        # 아이템 그리기 (이미지 크기 조정 제거)
        for item in items:
            if item_images[item["type"]]:
                screen.blit(item_images[item["type"]], item["pos"])  # 이미 크기가 조정된 이미지를 사용
            else:
                pygame.draw.rect(screen, (0, 255, 0), (*item["pos"], player_size, player_size))  # 기본 색상으로 크기 조정

        # 최종 보스 소행성 발사
        if boss and random.randint(1, 50) == 1:  # 보스가 랜덤하게 소행성 발사
            for _ in range(random.randint(2, 5)):  # 2~5개의 소행성 발사
                boss_comets.append(create_boss_comet())
        for comet in boss_comets[:]:
            comet["pos"][1] += speed  # 소행성은 아래로만 이동
            if comet["pos"][1] > HEIGHT:
                boss_comets.remove(comet)  # 화면 밖으로 나간 소행성 제거

        # 보스 이동 및 체력 표시
        if boss:
            # 보스는 고정된 위치에 머무름 (움직이지 않음)

            # 보스 체력 표시
            boss_health_text = font.render(f"Boss Health: {boss['health']}", True, RED)
            screen.blit(boss_health_text, (WIDTH // 2 - 100, boss["size"][1] + 10))  # 보스 아래에 체력 표시

            # 보스 체력 감소 및 처치 처리
            for bullet in bullets[:]:
                boss_rect = {"pos": boss["pos"], "size": boss["size"]}
                bullet_rect = {"pos": bullet["pos"], "size": (10, 20)}  # 총알 크기
                if check_collision(boss_rect, bullet_rect):
                    boss["health"] -= bullet["damage"]
                    bullets.remove(bullet)
                    if boss["health"] <= 0:  # 보스 처치
                        boss = None
                        show_message("보스를 처치했습니다!")

            # 보스 그리기
            if boss_image:
                scaled_boss = pygame.transform.scale(boss_image, boss["size"])  # 보스 크기 조정
                screen.blit(scaled_boss, boss["pos"])
            else:
                pygame.draw.rect(screen, (255, 0, 255), (*boss["pos"], *boss["size"]))  # 보스는 보라색

        # 총알 이동 및 충돌 처리
        for bullet in bullets[:]:
            bullet["pos"][1] -= bullet_speed  # 총알 위로 이동
            if bullet["pos"][1] < 0:
                bullets.remove(bullet)  # 화면 밖으로 나간 총알 제거
            else:
                for comet in comets[:]:
                    bullet_rect = {"pos": bullet["pos"], "size": (10, 20)}  # 총알 크기 딕셔너리로 변환
                    if check_collision(bullet_rect, comet):  # 충돌 체크
                        comet["health"] = comet.get("health", 500) - bullet["damage"]  # 체력 감소
                        if comet["health"] <= 0:  # 체력이 0 이하가 되면 제거
                            comets.remove(comet)
                        bullets.remove(bullet)  # 총알 제거
                        break

        # 소행성 그리기
        for comet in comets:
            if meteorite_image:
                scaled_meteorite = pygame.transform.scale(meteorite_image, comet["size"])  # 크기 조정
                screen.blit(scaled_meteorite, comet["pos"])
            else:
                pygame.draw.rect(screen, RED, (*comet["pos"], *comet["size"]))

        # 총알 그리기
        for bullet in bullets:
            if bullet_image:
                scaled_bullet = pygame.transform.scale(bullet_image, (10, 20))  # 총알 크기 조정
                screen.blit(scaled_bullet, bullet["pos"])
            else:
                pygame.draw.rect(screen, WHITE, (*bullet["pos"], 10, 20))  # 기본 총알 크기

        # 시간 정지 상태 처리
        if freeze_timer > 0:
            freeze_timer -= delta_time
            if freeze_timer <= 0:
                speed = 5  # 시간 정지 해제 후 속도 복원

        # 점수 및 라운드 표시 (라운드 표시 제거, 스코어만 표시)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        draw_hearts()  # 하트 그리기

        # 총알 충전 상태 업데이트
        bullet_charge = min(100, bullet_charge + bullet_charge_rate * delta_time)  # 충전 상태 증가 (최대 100)

        # 총알 충전 상태 그리기
        draw_bullet_charge()

        # 아이템 슬롯 표시 (아이템 이름 제거)
        for i, slot in enumerate(item_slots):
            slot_x = WIDTH - 150 + i * 50  # 슬롯 위치 (가로 간격 50)
            slot_y = 10
            slot_color = (0, 0, 255) if i == selected_slot else (255, 255, 255)  # 선택된 슬롯은 파란색 테두리
            slot_bg_color = (50, 50, 50)  # 슬롯 배경 색상 (회색)
            pygame.draw.rect(screen, slot_bg_color, (slot_x, slot_y, 30, 30))  # 슬롯 배경
            pygame.draw.rect(screen, slot_color, (slot_x - 2, slot_y - 2, 34, 34), 2)  # 테두리
            if slot:  # 슬롯에 아이템이 있을 경우 아이템 이미지를 표시
                screen.blit(item_images[slot], (slot_x, slot_y))

        # 플레이어 그리기 (투명화 및 축소 상태 반영)
        if spaceship_image:
            scaled_spaceship = pygame.transform.scale(spaceship_image, (player_size, player_size))
            screen.blit(scaled_spaceship, player_pos)
        else:
            player_surface = pygame.Surface((player_size, player_size), pygame.SRCALPHA)
            player_surface.fill((255, 255, 255, player_alpha))  # 알파값 적용
            screen.blit(player_surface, player_pos)

        # 플레이어 및 소행성, 적, 아이템 그리기
        for enemy in enemies:
            if enemy_spaceship_image:
                screen.blit(enemy_spaceship_image, enemy["pos"])
            else:
                pygame.draw.rect(screen, (0, 0, 255), (*enemy["pos"], enemy["size"], enemy["size"]))  # 적은 파란색
        for item in items:
            if item_images[item["type"]]:
                screen.blit(item_images[item["type"]], item["pos"])
            else:
                pygame.draw.rect(screen, (0, 255, 0), (*item["pos"], item["size"][0], item["size"][1]))  # 기본 색상
        for comet in boss_comets:
            if meteorite_image:
                screen.blit(meteorite_image, comet["pos"])
            else:
                pygame.draw.rect(screen, RED, (*comet["pos"], comet["size"], comet["size"]))  # 보스 소행성은 빨간색
        if boss:
            if boss_image:
                scaled_boss = pygame.transform.scale(boss_image, boss["size"])  # 보스 크기 조정
                screen.blit(scaled_boss, boss["pos"])
            else:
                pygame.draw.rect(screen, (255, 0, 255), (*boss["pos"], *boss["size"]))  # 보스는 보라색

        # 메시지 표시
        if message:
            message_text = font.render(message, True, WHITE)
            screen.blit(message_text, (WIDTH // 2 - message_text.get_width() // 2, HEIGHT - 50))  # 화면 하단 중앙에 표시

        # 화면 업데이트 (점수, 라운드, 슬롯이 최상단에 표시되도록)
        pygame.display.flip()
        clock.tick(30)

    # 게임 종료 및 재시작 처리
    if not running:
        screen.fill(BLACK)
        game_over_text = font.render("Game Over", True, RED)
        restart_text = font.render("R: Restart | E: Exit", True, WHITE)
        screen.blit(game_over_text, (WIDTH // 2 - 100, HEIGHT // 2 - 50))
        screen.blit(restart_text, (WIDTH // 2 - 150, HEIGHT // 2 + 10))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # R 키로 게임 재시작
                        # 게임 변수 초기화
                        score = 0
                        speed = 5
                        comets = []
                        enemies = []
                        items = []
                        bullets = []
                        boss = None
                        shield_active = False
                        invisibility_active = False
                        shrink_active = False
                        freeze_timer = 0
                        player_pos = [WIDTH // 2, HEIGHT - 2 * player_size]
                        item_slots = [None, None, None]
                        running = True
                        waiting = False
                    elif event.key == pygame.K_e:  # E 키로 게임 종료
                        pygame.quit()
                        sys.exit()

    # 보스 처치 후 선택 화면
    screen.fill(BLACK)
    restart_text = font.render("처음부터 다시 하려면 R을 누르세요", True, WHITE)
    exit_text = font.render("종료하려면 E를 누르세요", True, RED)
    screen.blit(restart_text, (WIDTH // 2 - 200, HEIGHT // 2 - 30))
    screen.blit(exit_text, (WIDTH // 2 - 200, HEIGHT // 2 + 30))
    pygame.display.flip()

    # R 또는 E 키 입력 대기
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # R 키로 처음부터 다시
                    waiting = False
                elif event.key == pygame.K_e:  # E 키로 종료
                    waiting = False  # 종료 화면 유지 후 루프 종료
                    pygame.quit()
                    sys.exit()

# pygame 종료
pygame.quit()
