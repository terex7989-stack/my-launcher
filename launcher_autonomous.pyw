import sys
import math
import random
import multiprocessing
import tkinter as tk

# Явные импорты, чтобы PyInstaller гарантированно упаковал все библиотеки внутрь .exe
import pygame
import vpython


def run_catch_game():
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Поймай падающие объекты")

    WHITE, BLACK, BLUE, RED = (255, 255, 255), (0, 0, 0), (0, 0, 255), (255, 0, 0)
    player_width, player_height = 100, 20
    player_x = WIDTH // 2 - player_width // 2
    player_y = HEIGHT - player_height - 10
    player_speed = 7

    object_width, object_height, object_speed = 30, 30, 5
    objects = []

    def add_new_object():
        return pygame.Rect(random.randint(0, WIDTH - object_width), -object_height, object_width, object_height)

    objects.append(add_new_object())
    score = 0
    font = pygame.font.SysFont("Arial", 30)
    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed
        player_x = max(0, min(WIDTH - player_width, player_x))

        for obj in objects:
            obj.y += object_speed

        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        for obj in objects[:]:
            if player_rect.colliderect(obj):
                score += 1
                objects.remove(obj)
            elif obj.y > HEIGHT:
                objects.remove(obj)

        if len(objects) < 5:
            objects.append(add_new_object())

        screen.fill(BLACK)
        pygame.draw.rect(screen, BLUE, player_rect)
        for obj in objects:
            pygame.draw.rect(screen, RED, obj)
        screen.blit(font.render(f"Счет: {score}", True, WHITE), (10, 10))
        pygame.display.flip()

    pygame.quit()


def run_torus_3d():
    pygame.init()
    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("3D Симуляция бублика")
    clock = pygame.time.Clock()

    class Slider:
        def __init__(self, x, y, width, height, min_val, max_val, initial, label, is_int=False):
            self.x, self.y, self.width, self.height = x, y, width, height
            self.min_val, self.max_val, self.value = min_val, max_val, initial
            self.label, self.is_int, self.dragging = label, is_int, False
            self.knob_radius = self.height // 2
            self.rect = pygame.Rect(x, y, width, height)
            self.knob_x = self.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.width

        def draw(self, surface, font):
            pygame.draw.line(surface, (200, 200, 200), (self.x, self.y + self.height // 2), (self.x + self.width, self.y + self.height // 2), 4)
            pygame.draw.circle(surface, (255, 100, 100), (int(self.knob_x), self.y + self.height // 2), self.knob_radius)
            display_val = int(self.value) if self.is_int else round(self.value, 2)
            surface.blit(font.render(f"{self.label}: {display_val}", True, (255, 255, 255)), (self.x, self.y - self.height))

        def handle_event(self, event):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
                self.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                clamped_x = max(self.x, min(event.pos[0], self.x + self.width))
                self.knob_x = clamped_x
                self.value = self.min_val + ((clamped_x - self.x) / self.width) * (self.max_val - self.min_val)
                if self.is_int:
                    self.value = int(round(self.value))

    polygon_count, fov, camera_distance = 24, 60, 5
    rot_speed_x, rot_speed_y, rot_speed_z = 0.01, 0.02, 0.0
    panel_width, panel_margin = 220, 10
    panel_x, panel_y = screen_width - panel_width - panel_margin, panel_margin
    slider_width, slider_height, slider_gap = panel_width - 20, 20, 40
    font = pygame.font.SysFont("Arial", 16)

    sliders = [
        Slider(panel_x + 10, panel_y + 10, slider_width, slider_height, 8, 64, polygon_count, "Polygons", True),
        Slider(panel_x + 10, panel_y + 10 + slider_gap, slider_width, slider_height, 30, 120, fov, "FOV", True),
        Slider(panel_x + 10, panel_y + 10 + slider_gap * 2, slider_width, slider_height, 3, 15, camera_distance, "Zoom", False),
        Slider(panel_x + 10, panel_y + 10 + slider_gap * 3, slider_width, slider_height, 0, 0.1, rot_speed_x, "RotX", False),
        Slider(panel_x + 10, panel_y + 10 + slider_gap * 4, slider_width, slider_height, 0, 0.1, rot_speed_y, "RotY", False),
        Slider(panel_x + 10, panel_y + 10 + slider_gap * 5, slider_width, slider_height, 0, 0.1, rot_speed_z, "RotZ", False),
    ]

    def compute_torus(n, R=2, r=1):
        vertices = []
        for i in range(n):
            theta = 2 * math.pi * i / n
            ring = []
            for j in range(n):
                phi = 2 * math.pi * j / n
                ring.append([(R + r * math.cos(theta)) * math.cos(phi), (R + r * math.cos(theta)) * math.sin(phi), r * math.sin(theta)])
            vertices.append(ring)
        return vertices

    torus_mesh = compute_torus(polygon_count)
    rot_x = rot_y = rot_z = 0.0

    def rotate_point(p, ax, ay, az):
        x, y, z = p
        y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
        x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
        x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
        return [x, y, z]

    def project_point(p, fov_val, dist):
        x, y, z = p
        f = (screen_width / 2) / math.tan(math.radians(fov_val) / 2)
        z = (z + dist) or 0.001
        factor = f / z
        return [int(x * factor + screen_width / 2), int(-y * factor + screen_height / 2)]

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for s in sliders:
                s.handle_event(event)

        if sliders[0].value != polygon_count:
            polygon_count = sliders[0].value
            torus_mesh = compute_torus(polygon_count)
        fov, camera_distance = sliders[1].value, sliders[2].value
        rot_x += sliders[3].value
        rot_y += sliders[4].value
        rot_z += sliders[5].value

        screen.fill((0, 0, 0))
        projected = [
            [project_point(rotate_point(torus_mesh[i][j], rot_x, rot_y, rot_z), fov, camera_distance) for j in range(polygon_count)]
            for i in range(polygon_count)
        ]
        for i in range(polygon_count):
            for j in range(polygon_count):
                pygame.draw.line(screen, (100, 255, 100), projected[i][j], projected[i][(j + 1) % polygon_count], 1)
                pygame.draw.line(screen, (100, 255, 100), projected[i][j], projected[(i + 1) % polygon_count][j], 1)

        panel_surface = pygame.Surface((panel_width, slider_gap * 6), pygame.SRCALPHA)
        panel_surface.fill((50, 50, 50, 200))
        screen.blit(panel_surface, (panel_x, panel_y))
        for s in sliders:
            s.draw(screen, font)
        pygame.display.flip()

    pygame.quit()


def run_3d_model():
    from vpython import sphere, cylinder, vector, color, scene, rate
    scene.title = "3D Модель персонажа"
    scene.background = color.white
    sphere(pos=vector(0, 2, 0), radius=0.5, color=color.yellow)
    cylinder(pos=vector(0, 1.2, 0), axis=vector(0, 0.8, 0), radius=0.3, color=color.red)
    cylinder(pos=vector(-0.3, 1.7, 0), axis=vector(-0.5, -0.3, 0), radius=0.1, color=color.red)
    cylinder(pos=vector(0.3, 1.7, 0), axis=vector(0.5, -0.3, 0), radius=0.1, color=color.red)
    cylinder(pos=vector(-0.15, 0.4, 0), axis=vector(0, -0.5, 0), radius=0.1, color=color.blue)
    cylinder(pos=vector(0.15, 0.4, 0), axis=vector(0, -0.5, 0), radius=0.1, color=color.blue)
    sphere(pos=vector(-0.15, 2.1, 0.45), radius=0.05, color=color.black)
    sphere(pos=vector(0.15, 2.1, 0.45), radius=0.05, color=color.black)
    sphere(pos=vector(0, 2.5, 0), radius=0.5, color=color.black, opacity=0.6)
    sphere(pos=vector(0.4, 2.4, 0), radius=0.3, color=color.black, opacity=0.6)
    sphere(pos=vector(-0.4, 2.4, 0), radius=0.3, color=color.black, opacity=0.6)
    while True:
        rate(60)


def run_2d_model():
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Персонаж на Python")
    WHITE, BLACK, SKIN, PINK, BLUE = (255, 255, 255), (0, 0, 0), (255, 224, 189), (255, 182, 193), (0, 0, 255)
    clock = pygame.time.Clock()

    def draw_girl(surface, cx, cy):
        head_center = (cx, cy - 80)
        pygame.draw.circle(surface, SKIN, head_center, 30)
        pygame.draw.circle(surface, BLACK, (cx - 10, cy - 85), 3)
        pygame.draw.circle(surface, BLACK, (cx + 10, cy - 85), 3)
        pygame.draw.rect(surface, BLACK, pygame.Rect(cx - 30, head_center[1] - 20, 60, 20))
        body_rect = pygame.Rect(cx - 20, head_center[1] + 30, 40, 80)
        pygame.draw.rect(surface, PINK, body_rect)
        pygame.draw.line(surface, SKIN, (body_rect.left, body_rect.top + 20), (body_rect.left - 30, body_rect.top + 40), 5)
        pygame.draw.line(surface, SKIN, (body_rect.right, body_rect.top + 20), (body_rect.right + 30, body_rect.top + 40), 5)
        pygame.draw.line(surface, BLUE, (cx - 10, body_rect.bottom), (cx - 10, body_rect.bottom + 50), 5)
        pygame.draw.line(surface, BLUE, (cx + 10, body_rect.bottom), (cx + 10, body_rect.bottom + 50), 5)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill(WHITE)
        draw_girl(screen, WIDTH // 2, HEIGHT // 2 + 50)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


def launch_process(target_func):
    p = multiprocessing.Process(target=target_func, daemon=True)
    p.start()


def open_dice_window(root):
    win = tk.Toplevel(root)
    win.title("Бросок кубиков")
    win.geometry("300x260")
    win.configure(bg="#1e1e2e")

    tk.Label(win, text="Сколько кубиков бросить?", fg="white", bg="#1e1e2e", font=("Arial", 11)).pack(pady=10)
    entry = tk.Entry(win, font=("Arial", 12), justify="center", width=10)
    entry.insert(0, "2")
    entry.pack(pady=5)

    res_label = tk.Label(win, text="", fg="#a6e3a1", bg="#1e1e2e", font=("Arial", 11), wraplength=260)
    res_label.pack(pady=15)

    def roll():
        try:
            n = int(entry.get())
            if n <= 0 or n > 50:
                res_label.config(text="Введите число от 1 до 50", fg="#f38ba8")
                return
            rolls = [random.randint(1, 6) for _ in range(n)]
            text = "\n".join([f"Кубик {i+1}:  🎲 {v}" for i, v in enumerate(rolls)])
            res_label.config(text=text, fg="#a6e3a1")
        except ValueError:
            res_label.config(text="Ошибка: введите целое число", fg="#f38ba8")

    tk.Button(win, text="Бросить!", command=roll, bg="#89b4fa", fg="#11111b", font=("Arial", 11, "bold"), width=15).pack(pady=5)


def main():
    root = tk.Tk()
    root.title("Центр мини-программ")
    root.geometry("380x410")
    root.configure(bg="#1e1e2e")
    root.resizable(False, False)

    tk.Label(root, text="Выберите программу", fg="#cdd6f4", bg="#1e1e2e", font=("Arial", 16, "bold")).pack(pady=20)

    btn_style = {
        "font": ("Arial", 11, "bold"),
        "width": 30,
        "height": 2,
        "bg": "#313244",
        "fg": "white",
        "bd": 0,
        "cursor": "hand2",
    }

    tk.Button(root, text="🎮  1. Игра: Поймай объекты", command=lambda: launch_process(run_catch_game), **btn_style).pack(pady=6)
    tk.Button(root, text="🍩  2. 3D-симуляция бублика", command=lambda: launch_process(run_torus_3d), **btn_style).pack(pady=6)
    tk.Button(root, text="🧍  3. 3D-модель в браузере", command=lambda: launch_process(run_3d_model), **btn_style).pack(pady=6)
    tk.Button(root, text="🎲  4. Бросок игральных кубиков", command=lambda: open_dice_window(root), **btn_style).pack(pady=6)
    tk.Button(root, text="🎨  5. 2D-рисунок персонажа", command=lambda: launch_process(run_2d_model), **btn_style).pack(pady=6)

    root.mainloop()


if __name__ == "__main__":
    # Обязательно для корректной работы multiprocessing внутри собранного .exe на Windows
    multiprocessing.freeze_support()
    main()
