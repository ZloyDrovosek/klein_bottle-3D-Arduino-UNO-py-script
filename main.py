import os
import sys
import time
import math
import pygame
import serial
import serial.tools.list_ports

BAUD_RATE = 115200

def select_com_port():
    """Показывает список всех портов и просит пользователя выбрать нужный"""
    print("\n=== ПОИСК УСТРОЙСТВ ===")
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("❌ Компьютер не видит ни одного COM-порта! Проверь USB-кабель.")
        input("Нажми Enter для выхода...")
        sys.exit()
        
    print("Доступные порты:")
    for i, port in enumerate(ports):
        print(f" [{i}] {port.device} — {port.description}")
        
    while True:
        try:
            choice = int(input("\nВведите номер порта для подключения Arduino: "))
            if 0 <= choice < len(ports):
                target_port = ports[choice].device
                print(f"🔗 Подключаемся к {target_port}...")
                
                ser = serial.Serial(target_port, BAUD_RATE, timeout=0.1)
                time.sleep(2) # Пауза на перезагрузку платы
                print("✅ Успешно сопряжено!")
                return ser
            else:
                print("Неверный номер. Попробуй еще раз.")
        except ValueError:
            print("Введите корректное число.")
        except serial.SerialException:
            print("❌ Этот порт занят другой программой! Закрой Arduino IDE и попробуй снова.")

# 1. Запуск выбора порта прямо в консоли
arduino_serial = select_com_port()

# 2. Старт графического движка Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Klein Bottle — Новая сборка")
clock = pygame.time.Clock()

SCALE = 45          
DISTANCE = 5        
A = 0.0 # Вращение по оси X (автоматическое)
B = 0.0 # Вращение по оси Y (от Ардуино)

def get_klein_point(u, v):
    """Математическая формула бутылки Клейна"""
    cos_u, sin_u = math.cos(u), math.sin(u)
    cos_v, sin_v = math.cos(v), math.sin(v)
    if u < math.pi:
        x = 3 * cos_u * (1 + sin_u) + (2 * (1 - cos_u / 2)) * cos_u * cos_v
        z = -8 * sin_u - (2 * (1 - cos_u / 2)) * sin_u * cos_v
    else:
        x = 3 * cos_u * (1 + sin_u) + (2 * (1 - cos_u / 2)) * cos_v * math.cos(u + math.pi)
        z = -8 * sin_u
    y = (2 * (1 - cos_u / 2)) * sin_v
    return x, -y, z

# Главный игровой цикл
running = True
while running:
    clock.tick(60)
    screen.fill((15, 15, 25)) # Свежий темно-синий фон
    
    # Отслеживаем закрытие окна
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 3. Чтение данных из Ардуино через безопасный буфер in_waiting
    if arduino_serial.in_waiting > 0: 
        try:
            line = arduino_serial.readline().decode('utf-8').strip()
            if line:
                B = float(line) # Управляем углом B
        except (ValueError, Exception):
            pass # Пропускаем битые пакеты данных

    A += 0.015 # Авто-вращение по X
    
    # Подготовка тригонометрии кадра
    sinA, cosA = math.sin(A), math.cos(A)
    sinB, cosB = math.sin(B), math.cos(B)
    
    # Инициализация Z-буфера под размер экрана
    z_buffer = [[0.0 for _ in range(HEIGHT)] for _ in range(WIDTH)]
    u_step, v_step = 0.1, 0.1
    
    # Рендеринг 3D геометрии
    u = 0.0
    while u < 2 * math.pi:
        v = 0.0
        while v < 2 * math.pi:
            x, y, z = get_klein_point(u, v)
            
            # Вращение точек по двум осям
            y1 = y * cosA - z * sinA
            z1 = y * sinA + z * cosA
            x2 = x * cosB + z1 * sinB
            z2 = -x * sinB + z1 * cosB
            y2 = y1
            
            # Проекция перспективы (глубина)
            ooz = 1 / (z2 + DISTANCE)
            xp = int(WIDTH / 2 + x2 * SCALE * ooz * 1.5)
            yp = int(HEIGHT / 2 + y2 * SCALE * ooz)
            
            # Если точка попала на экран
            if 0 <= xp < WIDTH and 0 <= yp < HEIGHT:
                # Расчет псевдо-освещения
                luminance = int(math.cos(u) * math.cos(v) * 127 + 128)
                depth_shade = (z2 + 10) / 20 
                brightness = max(15, min(255, int(luminance * depth_shade)))
                
                # Проверка перекрытия слоев (Z-буфер)
                if ooz > z_buffer[xp][yp]:
                    z_buffer[xp][yp] = ooz
                    
                    # Плавный неоновый цвет (смесь фиолетового и бирюзы)
                    r = int(brightness * (math.sin(u) * 0.4 + 0.6))
                    g = int(brightness * (math.cos(v) * 0.4 + 0.6))
                    b = brightness
                    
                    screen.set_at((xp, yp), (r, g, b))
            v += v_step
        u += u_step

    pygame.display.flip()

# Чистим ресурсы перед выходом
arduino_serial.close()
pygame.quit()
sys.exit()
