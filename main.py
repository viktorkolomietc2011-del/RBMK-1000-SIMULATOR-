# ========== ЧАСТЬ 1: ИМПОРТЫ И НАСТРОЙКИ ==========
import math
import random
import pygame
import os

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Симулятор БЩУ РБМК-1000 [Научно-физическая версия]")
clock = pygame.time.Clock()
# ========== КОНЕЦ ЧАСТИ 1 ==========
# ========== ЧАСТЬ 2: ШРИФТЫ, ЗВУКИ, ЦВЕТА, КОНСТАНТЫ ==========
font_small = pygame.font.Font(None, 11)
font = pygame.font.Font(None, 14)
font_bold = pygame.font.Font(None, 16); font_bold.set_bold(True)
font_large = pygame.font.Font(None, 24); font_large.set_bold(True)
font_huge = pygame.font.Font(None, 48); font_huge.set_bold(True)
font_menu = pygame.font.Font(None, 36); font_menu.set_bold(True)
font_title = pygame.font.Font(None, 72); font_title.set_bold(True)

sounds = {}
try:
    if os.path.exists("explosion.wav"): sounds['explosion'] = pygame.mixer.Sound("explosion.wav")
    if os.path.exists("evac.wav"): sounds['evac'] = pygame.mixer.Sound("evac.wav")
    if os.path.exists("click.wav"): sounds['click'] = pygame.mixer.Sound("click.wav")
    if os.path.exists("beep.wav"): sounds['beep'] = pygame.mixer.Sound("beep.wav")
    if os.path.exists("loop.wav"): 
        sounds['loop'] = pygame.mixer.Sound("loop.wav")
        sounds['loop'].play(-1)
    if os.path.exists("Alert.wav"):
        sounds['alert'] = pygame.mixer.Sound("Alert.wav")
except Exception:
    pass

try:
    menu_bg_img = pygame.image.load("1000682396.jpg").convert()
    menu_bg_img = pygame.transform.scale(menu_bg_img, (WIDTH, HEIGHT))
except Exception:
    menu_bg_img = pygame.Surface((WIDTH, HEIGHT))
    menu_bg_img.fill((30, 40, 30))

def play_sound(name):
    if name in sounds: 
        try:
            sounds[name].play()
        except:
            pass

def stop_sound(name):
    if name in sounds:
        try:
            sounds[name].stop()
        except:
            pass

evac_started = False
COLOR_PANEL = (135, 150, 138)
COLOR_PANEL_DARK = (115, 130, 118)
COLOR_FRAME = (75, 85, 78)
COLOR_TEXT_DARK = (20, 25, 20)

# Физические константы
POWER_TIME_CONST = 10.0
RHO_RODS_COEFF = 0.0008
RHO_XE_COEFF = 0.0012
RHO_TEMP_COEFF = 0.00018
RHO_STEAM_COEFF = 0.0012

# Ксенон (реалистичный, ~18 минут до 100%)
IODINE_PROD = 0.445
IODINE_DECAY = 0.005
XENON_FROM_IODINE = 0.00113
XENON_DECAY = 0.002
XENON_BURN = 0.0018

FUEL_TEMP_COEFF = 0.09
FUEL_TEMP_SPEED = 0.04
COOLING_BASE = 9.3
BEARING_HEAT_RATE_BASE = 0.05
BEARING_HEAT_PER_PUMP = 0.06
BEARING_COOL_SPEED = 0.01
ROD_END_EFFECT = 0.045
MAX_POWER = 45000.0
MAX_FUEL_TEMP = 3500.0
BEARING_CRITICAL = 500.0
STEAM_EXPLOSION_LIMIT = 85.0
PRESSURE_EXPLOSION_LIMIT = 12.0

# ПЭН и масло
PEN_OIL_NORMAL = 40.0
PEN_OIL_CRITICAL = 80.0
PEN_OIL_HEAT_RATE = 0.33
PEN_OIL_COOL_RATE = 0.1

STEAM_GROWTH_MULTIPLIER = 0.67
STEAM_SPEED = 0.05

# Скрытая поломка
HIDDEN_EXPLOSION_DELAY = 20.0
HIDDEN_POWER_TARGET = 30000.0
HIDDEN_POWER_RISE_TIME = 3.0

# БС
BS_NORMAL = 0.0
BS_MAX = 1500.0
BS_MIN = -1500.0
BS_CRITICAL_PLUS = 1200.0
BS_CRITICAL_MINUS = -1200.0
BS_AUTO_SPEED = 0.5
BS_MANUAL_SPEED = 50.0
BS_PEN_OFF_DROP_RATE = 4.0

# БРУ-К
BRU_OPEN = 1.0
BRU_CLOSED = 0.0
BRU_OVERHEAT_TIME = 8.0
BRU_ESCAPE_COEFF = 0.8

# Дизель-генератор
DG_START_TIME = 45.0          # секунд на запуск
DG_FUEL_CAPACITY = 10.0       # минут работы
DG_FUEL_CONSUMPTION = 1.0 / 600.0  # расход за секунду
DG_POWER_OUTPUT = 50.0        # МВт, выдаваемых при работе
# ========== КОНЕЦ ЧАСТИ 2 ==========
# ========== ЧАСТЬ 3: КЛАСС REACTORSIMULATOR (КОНСТРУКТОР, BUILD_CORE_MAP) ==========
class ReactorSimulator:
    def __init__(self):
        self.build_core_map()
        self.reset_normal()
        self.shake_intensity = 0.0
        self.flash_intensity = 0.0
        self.explosion_phase = 0
        self.console_text = ""
        self.console_visible = False
        self.console_progress = 0
        self.console_timer = 0.0
        self.explosion_timer = 0.0
        self.end_type = "none"
        self.explosion_particles = []
        self.siren_enabled = True
        self.siren_playing = False
        self.explosion_shake_boost = 1.0
        self.pen_enabled = True
        self.pen_manual_override = False
        self.oil_temp = 40.0
        self.oil_damage_done = False

        self.hidden_mode_active = False
        self.display_frozen = False
        self.hidden_timer = 0.0
        self.hidden_power = 0.0
        self.hidden_fuel_temp = 0.0
        self.hidden_steam_fraction = 0.0
        self.trigger_sequence = 0
        self.cheat_hidden = False

        # БС
        self.bs_auto = True
        self.bs_level = BS_NORMAL
        self.bs_target = BS_NORMAL
        self.bs_manual_plus = False
        self.bs_manual_minus = False
        self.bs_damage_done_plus = False
        self.bs_damage_done_minus = False

        # БРУ-К
        self.bru_enabled = False
        self.bru_open = BRU_CLOSED
        self.bru_overheat_timer = 0.0
        self.bru_closed_by_protection = False

        # Дизель-генератор
        self.dg_enabled = False
        self.dg_running = False
        self.dg_fuel = DG_FUEL_CAPACITY
        self.dg_start_timer = 0.0

        # Миссии
        self.mission_mode = False
        self.mission_id = 0
        self.mission_completed = False
        self.mission_failed = False
        self.mission_console_text = ""

    def build_core_map(self):
        self.core_map = []
        self.core_dict = {}
        cx, cy = 260, 245  
        grid_w = 27       
        cell_size = 11
        spacing = 4
        radius = 11 * (cell_size + spacing)
        letters = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"[:grid_w]
        for y in range(grid_w):
            for x in range(grid_w):
                px = cx + (x - grid_w//2) * (cell_size + spacing)
                py = cy + (y - grid_w//2) * (cell_size + spacing)
                dist = math.hypot(px - cx, py - cy)
                if dist < radius:
                    ctype = "fuel"
                    base_color = [170, 175, 165] 
                    if (x + y) % 6 == 0 and x % 2 == 0:
                        ctype, base_color = "az", [220, 40, 40]
                    elif (x + y) % 7 == 0:
                        ctype, base_color = "ar", [40, 180, 60]
                    elif (x - y) % 5 == 0:
                        ctype, base_color = "usp", [230, 210, 30]
                    elif (x * y) % 11 == 0:
                        ctype, base_color = "lar", [240, 240, 240] 
                    elif (x + y) % 9 == 0:
                        ctype, base_color = "pk", [40, 100, 220] 
                    cell_data = {
                        "grid_x": x, "grid_y": y,
                        "coord_name": f"{letters[x]}-{y+1:02d}",
                        "x": px, "y": py, "type": ctype, "color": base_color,
                        "power": random.randint(90, 110),
                        "temp": 300.0
                    }
                    self.core_map.append(cell_data)
                    self.core_dict[(x, y)] = cell_data
        self.selected_grid_pos = (13, 13)
        self.filter_mode = "ALL"
        self.event_log = ["11:00:00 - БЩУ: Режим нормальной работы активирован"]
        self.shift_timer = 0.0

    def add_log(self, text):
        hours = int(self.shift_timer // 3600) + 11
        minutes = int((self.shift_timer % 3600) // 60)
        seconds = int(self.shift_timer % 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.event_log.append(f"{timestamp} - {text}")
        if len(self.event_log) > 50:
            self.event_log.pop(0)
# ========== КОНЕЦ ЧАСТИ 3 ==========
# ========== ЧАСТЬ 4: REACTORSIMULATOR – RESET_NORMAL, ПРЕСЕТЫ И МИССИИ ==========
    def reset_normal(self):
        self.power = 3200.0
        self.elec_power = 1000.0
        self.power_vel = 0.0
        self.rods_pos = 50.0
        self.iodine = 15.0
        self.xenon = 15.0
        self.ozr = 30.0
        self.display_ozr = 30.0
        self.fuel_temp = 555.7
        self.inlet_temp = 280.5
        self.steam_fraction = 9.3
        self.feed_water_flow = 3200.0
        self.bs_level = BS_NORMAL
        self.bs_target = BS_NORMAL
        self.bs_auto = True
        self.bs_manual_plus = False
        self.bs_manual_minus = False
        self.bs_damage_done_plus = False
        self.bs_damage_done_minus = False
        self.bs_pressure = 7.0
        self.ar_active = True
        self.station_power = True
        self.gcn_count = 8
        self.gcn_speed = 8.0
        self.gcn_bearing_temp = 50.0
        self.prot_water = True
        self.prot_ozr = True
        self.turbine_coasting = False
        self.az5_locked_out = False
        self.az5_reset_pressed = True
        self.xenon_poison_timer = 0.0
        self.residual_heat_temp = 300.0
        self.fuel_melted = False
        self.xenon_pit_active = False
        self.chernobyl_explosion = False
        self.steam_explosion_active = False
        self.restart_mode = False
        self.scala_state = "IDLE"
        self.scala_timer = 0.0
        self.tg7_prot = True
        self.tg8_prot = True
        self.az5_cap_open = False
        self.az5_active = False
        self.is_exploding = False
        self.cheat_boom_ready = False
        self.cheat_steam_ready = False
        self.cheat_shutdown = False
        self.cheat_hidden = False
        self.override_cap_open = False
        self.override_key_inserted = False
        self.override_key_turned = False
        self.lar_positions = [50.0] * 10
        self.pyatachok = [True, True, True, True]
        self.anim_angles = {"tg7": 45.0, "tg8": 45.0, "bs_auto": 45.0, "ar": 45.0, "gcn": 45.0, "p_water": 45.0, "p_ozr": 45.0, "tg_coast": -45.0, "pen": 45.0, "bru": -45.0, "dg": -45.0}
        self.shake_intensity = 0.0
        self.flash_intensity = 0.0
        self.explosion_phase = 0
        self.console_visible = False
        self.console_progress = 0
        self.console_timer = 0.0
        self.explosion_timer = 0.0
        self.end_type = "none"
        self.explosion_particles = []
        self.siren_enabled = True
        self.siren_playing = False
        self.explosion_shake_boost = 1.0
        self.pen_enabled = True
        self.pen_manual_override = False
        self.oil_temp = 40.0
        self.oil_damage_done = False
        self.hidden_mode_active = False
        self.display_frozen = False
        self.hidden_timer = 0.0
        self.hidden_power = 0.0
        self.hidden_fuel_temp = 0.0
        self.hidden_steam_fraction = 0.0
        self.trigger_sequence = 0
        self.cheat_hidden = False
        self.bru_enabled = False
        self.bru_open = BRU_CLOSED
        self.bru_overheat_timer = 0.0
        self.bru_closed_by_protection = False
        self.dg_enabled = False
        self.dg_running = False
        self.dg_fuel = DG_FUEL_CAPACITY
        self.dg_start_timer = 0.0

        self.mission_mode = False
        self.mission_id = 0
        self.mission_completed = False
        self.mission_failed = False
        self.mission_console_text = ""

        stop_sound('alert')
        self.add_log("Система СКАЛА: Параметры реактора сброшены в норму")

    def set_hidden_prep(self):
        self.reset_normal()
        self.power = 3200.0
        self.rods_pos = 0.0
        self.ar_active = False
        self.tg7_prot = False
        self.tg8_prot = False
        self.az5_active = True
        self.az5_cap_open = True
        self.turbine_coasting = True
        self.cheat_hidden = True
        self.trigger_sequence = 3
        self.hidden_mode_active = True
        self.display_frozen = True
        self.hidden_timer = 0.0
        self.hidden_power = self.power
        self.hidden_fuel_temp = self.fuel_temp
        self.hidden_steam_fraction = self.steam_fraction
        self.add_log("ВНИМАНИЕ: Активирован чит-режим «ПОЛОМКА БЩУ» (Скрытый разгон)")

    def set_boom_prep(self):
        self.reset_normal()
        self.power = 200.0
        self.xenon = 100.0
        self.rods_pos = 0.0
        self.ar_active = False
        self.ozr = 0.0
        self.display_ozr = 0.0
        self.cheat_boom_ready = True
        self.cheat_steam_ready = False
        self.cheat_shutdown = False
        self.cheat_hidden = False
        self.az5_cap_open = True
        self.prot_ozr = False
        self.turbine_coasting = True
        self.add_log("ВНИМАНИЕ: Активирован чит-режим «ВЗРЫВ» (Физический разгон РБМК)!")

    def set_steam_prep(self):
        self.reset_normal()
        self.power = 4000.0
        self.steam_fraction = 90.0
        self.bs_pressure = 15.0
        self.ar_active = False
        self.cheat_steam_ready = True
        self.cheat_boom_ready = False
        self.cheat_shutdown = False
        self.cheat_hidden = False
        self.add_log("ВНИМАНИЕ: Активирован чит-режим «ПАРОВОЙ ВЗРЫВ»!")

    def set_blackout_prep(self):
        self.reset_normal()
        self.power = 400.0
        self.rods_pos = 65.0
        self.tg7_prot = False
        self.tg8_prot = False
        self.cheat_shutdown = False
        self.cheat_hidden = False
        self.add_log("ВНИМАНИЕ: Подготовка к полному блэкауту станции")

    def set_melt_prep(self):
        self.reset_normal()
        self.power = 3200.0
        self.az5_active = True
        self.gcn_count = 0
        self.station_power = False
        self.residual_heat_temp = 2750.0
        self.cheat_shutdown = False
        self.cheat_hidden = False
        self.add_log("ВНИМАНИЕ: Активирован чит-режим «Китайский синдром» (Расплавление зоны)")

    def set_xenon_prep(self):
        self.reset_normal()
        self.power = 50.0
        self.xenon = 95.0
        self.ozr = 0.0
        self.display_ozr = 0.0
        self.cheat_shutdown = False
        self.cheat_hidden = False
        self.add_log("ВНИМАНИЕ: Активирован чит-режим «Ксеноновая яма»")

    def set_bearing_prep(self):
        self.reset_normal()
        self.gcn_count = 0
        self.station_power = False
        self.gcn_bearing_temp = 510.0
        self.cheat_shutdown = False
        self.cheat_hidden = False
        self.add_log("ВНИМАНИЕ: Активирован чит-режим «Перегрев подшипников ГЦН»")

    def set_shutdown_prep(self):
        self.reset_normal()
        self.power = 0.0
        self.rods_pos = 100.0
        self.ar_active = False
        self.gcn_count = 0
        self.station_power = False
        self.tg7_prot = False
        self.tg8_prot = False
        self.cheat_shutdown = True
        self.cheat_boom_ready = False
        self.cheat_steam_ready = False
        self.cheat_hidden = False
        self.add_log("РЕАКТОР ОСТАНОВЛЕН (ЧИТ). Требуется запуск.")

    def set_startup_prep(self):
        self.reset_normal()
        self.power = 5.0
        self.rods_pos = 100.0
        self.ar_active = False
        self.gcn_count = 0
        self.station_power = False
        self.tg7_prot = False
        self.tg8_prot = False
        self.cheat_shutdown = True
        self.cheat_boom_ready = False
        self.cheat_steam_ready = False
        self.cheat_hidden = False
        self.add_log("РЕАКТОР В РЕЖИМЕ ПУСКА. Поднимите стержни СУЗ и включите ГЦН.")

    def restart_reactor(self):
        if self.gcn_count >= 4 and self.az5_reset_pressed and self.power < 50.0:
            self.az5_active = False
            self.az5_locked_out = False
            self.restart_mode = False
            self.cheat_shutdown = False
            self.cheat_hidden = False
            self.hidden_mode_active = False
            self.display_frozen = False
            self.add_log("СИСТЕМА: Сигнал АЗ-5 сброшен. Управление разблокировано. Выполняйте пуск.")
        else:
            self.add_log("ОШИБКА ПУСКА: Проверьте ГЦН (>=4), нажмите сброс АЗ-5 и дождитесь мощности <50 МВт.")

    # ---- МЕТОДЫ ДЛЯ МИССИЙ ----
    def set_mission(self, mission_id):
        self.mission_mode = True
        self.mission_id = mission_id
        self.mission_completed = False
        self.mission_failed = False
        self.mission_console_text = ""
        self.shake_intensity = 0.0
        self.flash_intensity = 0.0
        self.explosion_phase = 0
        self.console_visible = False
        self.is_exploding = False
        self.end_type = "none"

        if mission_id == 1:  # Разогнать до 4000
            self.reset_normal()
            self.power = 3200.0
            self.elec_power = 1000.0
        elif mission_id == 2:  # Спустить до 2000
            self.reset_normal()
            self.power = 4000.0
            self.elec_power = 1250.0
            self.power_vel = 50.0
            self.rods_pos = 20.0
        elif mission_id == 3:  # Перейти на ДГ
            self.reset_normal()
            self.power = 3200.0
            self.tg7_prot = True
            self.tg8_prot = True
            self.dg_enabled = False
            self.dg_running = False
            self.dg_fuel = DG_FUEL_CAPACITY
        elif mission_id == 4:  # Поднять БС до 1000
            self.reset_normal()
            self.bs_auto = True
            self.bs_level = 0.0
        elif mission_id == 5:  # Взорвать реактор
            self.reset_normal()
        elif mission_id == 6:  # Запустить реактор
            self.reset_normal()
            self.power = 0.0
            self.rods_pos = 100.0
            self.gcn_count = 0
            self.gcn_speed = 0.0
            self.ar_active = False
            self.tg7_prot = True
            self.tg8_prot = True
            self.station_power = False
            self.pen_enabled = False
            self.feed_water_flow = 0.0

        self.add_log(f"Запущена миссия {mission_id}")

    def check_mission(self):
        if self.mission_completed or self.mission_failed:
            return

        if self.mission_id == 1:
            if self.power >= 4000:
                self.mission_completed = True
                self.mission_console_text = "Задание выполнено! Реактор разогнан до 4000 МВт."
            elif self.is_exploding:
                self.mission_failed = True
                self.mission_console_text = "Задание провалено! Реактор взорвался."
        elif self.mission_id == 2:
            if self.power <= 2000:
                self.mission_completed = True
                self.mission_console_text = "Задание выполнено! Реактор снижен до 2000 МВт."
            elif self.is_exploding:
                self.mission_failed = True
                self.mission_console_text = "Задание провалено! Реактор взорвался."
        elif self.mission_id == 3:
            if not self.tg7_prot and not self.tg8_prot and self.dg_running:
                self.mission_completed = True
                self.mission_console_text = "Задание выполнено! Свет переведён на ДГ."
            elif self.is_exploding:
                self.mission_failed = True
                self.mission_console_text = "Задание провалено! Реактор взорвался."
        elif self.mission_id == 4:
            if self.bs_level >= 1000:
                self.mission_completed = True
                self.mission_console_text = "Задание выполнено! Уровень БС поднят до 1000 мм."
            elif self.is_exploding:
                self.mission_failed = True
                self.mission_console_text = "Задание провалено! Реактор взорвался."
        elif self.mission_id == 5:
            if self.is_exploding:
                self.mission_completed = True
                self.mission_console_text = "Задание выполнено! Реактор взорван успешно."
        elif self.mission_id == 6:
            if self.power >= 3100 and self.power <= 3300 and self.rods_pos < 10 and self.gcn_count >= 4:
                self.mission_completed = True
                self.mission_console_text = "Задание выполнено! Реактор успешно запущен."
            elif self.is_exploding:
                self.mission_failed = True
                self.mission_console_text = "Задание провалено! Реактор взорвался."

        if self.mission_completed or self.mission_failed:
            self.console_visible = True
            self.console_text = self.mission_console_text
            self.end_type = "mission"
            self.console_progress = 0
            self.console_timer = 0.0
# ========== КОНЕЦ ЧАСТИ 4 ==========
# ========== ЧАСТЬ 5: REACTORSIMULATOR – UPDATE (ФИЗИКА, ЧАСТЬ 1) ==========
    def update(self, dt):
        global evac_started
        self.shift_timer += dt

        targets = {
            "tg7": 45.0 if self.tg7_prot else -45.0,
            "tg8": 45.0 if self.tg8_prot else -45.0,
            "bs_auto": 45.0 if self.bs_auto else -45.0,
            "ar": 45.0 if self.ar_active else -45.0,
            "gcn": -45.0 + (self.gcn_count / 8.0) * 90.0,
            "p_water": 45.0 if self.prot_water else -45.0,
            "p_ozr": 45.0 if self.prot_ozr else -45.0,
            "tg_coast": 45.0 if self.turbine_coasting else -45.0,
            "pen": 45.0 if self.pen_enabled else -45.0,
            "bru": 45.0 if self.bru_enabled else -45.0,
            "dg": 45.0 if self.dg_enabled else -45.0
        }
        for k in self.anim_angles:
            if k in targets:
                self.anim_angles[k] += (targets[k] - self.anim_angles[k]) * 10.0 * dt

        if self.scala_state == "CALCULATING":
            self.scala_timer += dt
            if self.scala_timer >= 2.5:
                self.display_ozr = round(self.ozr, 1)
                self.scala_state = "IDLE"
                play_sound('beep')
                self.add_log(f"СКАЛА: ОЗР рассчитан -> {self.display_ozr} ст.")

        if self.explosion_phase > 0 or self.console_visible:
            return

        # ---- СКРЫТАЯ ПОЛОМКА ----
        if self.hidden_mode_active:
            self.hidden_timer += dt
            if self.hidden_timer <= HIDDEN_POWER_RISE_TIME:
                progress = self.hidden_timer / HIDDEN_POWER_RISE_TIME
                self.hidden_power = 3200.0 + (HIDDEN_POWER_TARGET - 3200.0) * progress
            else:
                self.hidden_power = HIDDEN_POWER_TARGET
            cooling = max(0.05, self.gcn_speed / 8.0)
            target_fuel = 270.0 + self.hidden_power * FUEL_TEMP_COEFF / math.sqrt(cooling)
            self.hidden_fuel_temp += (target_fuel - self.hidden_fuel_temp) * FUEL_TEMP_SPEED * dt
            if self.pen_enabled and self.feed_water_flow > 0:
                target_steam = (self.hidden_power / 3200.0) * (1.0 / cooling) * COOLING_BASE
            else:
                target_steam = (self.hidden_power / 3200.0) * (1.0 / max(0.01, cooling)) * COOLING_BASE * STEAM_GROWTH_MULTIPLIER * 2.0
            self.hidden_steam_fraction += (target_steam - self.hidden_steam_fraction) * STEAM_SPEED * dt
            self.hidden_steam_fraction = min(100.0, max(0.0, self.hidden_steam_fraction))
            if self.hidden_power > 12000.0 or self.hidden_fuel_temp > 3500.0 or self.hidden_steam_fraction > 85.0:
                if self.hidden_timer >= HIDDEN_EXPLOSION_DELAY:
                    self.is_exploding = True
                    self.end_type = "hidden_explosion"
                    self.explosion_phase = 1
                    self.explosion_timer = 0.0
                    if 'loop' in sounds:
                        try: sounds['loop'].stop()
                        except: pass
                    play_sound('explosion')
                    self.add_log("КРИТИЧЕСКАЯ АВАРИЯ: Тепловой взрыв реактора. БЩУ уничтожен!")
                    return
            return

        # ---- ЛОГИКА ДИЗЕЛЬ-ГЕНЕРАТОРА ----
        if self.dg_enabled and not self.dg_running and self.dg_fuel > 0:
            self.dg_start_timer += dt
            if self.dg_start_timer >= DG_START_TIME:
                self.dg_running = True
                self.dg_start_timer = 0.0
                self.add_log("Дизель-генератор запущен")
        if self.dg_running:
            self.dg_fuel -= DG_FUEL_CONSUMPTION * dt
            if self.dg_fuel <= 0:
                self.dg_fuel = 0
                self.dg_running = False
                self.dg_enabled = False
                self.add_log("Дизель закончился! ДГ остановлен")
        if not self.dg_enabled and self.dg_running:
            self.dg_running = False
            self.dg_start_timer = 0.0
            self.add_log("Дизель-генератор выключен вручную")
        if self.dg_fuel <= 0:
            self.dg_enabled = False
            self.dg_running = False

        # ---- ЛОГИКА ПИТАНИЯ СТАНЦИИ (ИСПРАВЛЕННАЯ) ----
        # Если ДГ работает – питание есть всегда
        if self.dg_running and self.dg_fuel > 0:
            self.station_power = True
        else:
            # Если выработка электроэнергии упала до нуля – блэкаут
            if self.elec_power < 0.5 and not self.dg_running:
                if self.station_power:
                    self.station_power = False
                    self.add_log("АВАРИЯ: Полная потеря электроэнергии! Блэкаут!")
            # Если оба ТГ отключены и мощность упала – блэкаут (но только если нет ДГ)
            elif not self.tg7_prot and not self.tg8_prot and self.power < 500.0 and not self.dg_running:
                if self.station_power:
                    self.station_power = False
                    self.add_log("АВАРИЯ: Полная потеря собственных нужд и блэкаут!")
            else:
                # Восстановление питания, если есть работающие ТГ (независимо от ГЦН)
                # ИСПРАВЛЕНИЕ: убрана зависимость от `gcn_count`
                if not self.oil_damage_done and not self.bs_damage_done_plus and (self.tg7_prot or self.tg8_prot):
                    self.station_power = True
                else:
                    # Если нет ТГ и нет ДГ, то питания нет
                    if not self.dg_running:
                        self.station_power = False

        # ---- ЭЛЕКТРОГЕНЕРАЦИЯ (ускорено обновление) ----
        if self.dg_running:
            self.elec_power += (DG_POWER_OUTPUT - self.elec_power) * 0.1 * dt

        # ---- ЛОГИКА БРУ-К ----
        if self.bru_enabled:
            self.bru_open = BRU_OPEN
            self.elec_power = 0.0
            if self.tg7_prot or self.tg8_prot:
                self.bru_enabled = False
                self.bru_open = BRU_CLOSED
                self.add_log("БРУ-К отключен (защита: ТГ включены)")
        else:
            self.bru_open = BRU_CLOSED

        if self.az5_active:
            self.power *= (1.0 - 0.01 * dt)

        # ---- ЛОГИКА БС (уровень) ----
        if not self.pen_enabled:
            self.bs_level -= BS_PEN_OFF_DROP_RATE * dt
            self.bs_level = max(BS_MIN, self.bs_level)

        if self.bs_auto and self.pen_enabled:
            if self.bs_level > BS_NORMAL:
                self.bs_level -= BS_AUTO_SPEED * dt
                if self.bs_level < BS_NORMAL:
                    self.bs_level = BS_NORMAL
            elif self.bs_level < BS_NORMAL:
                self.bs_level += BS_AUTO_SPEED * dt
                if self.bs_level > BS_NORMAL:
                    self.bs_level = BS_NORMAL

        if not self.bs_auto:
            if self.bs_manual_plus:
                self.bs_level += BS_MANUAL_SPEED * dt
            if self.bs_manual_minus:
                self.bs_level -= BS_MANUAL_SPEED * dt

        self.bs_level = max(BS_MIN, min(BS_MAX, self.bs_level))

        if self.bs_level >= BS_CRITICAL_PLUS and not self.bs_damage_done_plus:
            self.bs_damage_done_plus = True
            self.tg7_prot = False
            self.tg8_prot = False
            self.station_power = False
            self.add_log("КРИТИЧЕСКАЯ ПОЛОМКА: Уровень БС достиг +1200 мм! ТГ-7 и ТГ-8 вышли из строя НЕОБРАТИМО! Блэкаут!")

        if self.bs_level <= BS_CRITICAL_MINUS and not self.bs_damage_done_minus:
            self.bs_damage_done_minus = True
            self.gcn_count = 0
            self.gcn_speed = 0.0
            self.add_log("КРИТИЧЕСКАЯ ПОЛОМКА: Уровень БС достиг -1200 мм! Все ГЦН остановлены НЕОБРАТИМО!")

        # ---- ПЭН И МАСЛО ----
        if self.pen_enabled:
            self.oil_temp += (PEN_OIL_NORMAL - self.oil_temp) * PEN_OIL_COOL_RATE * dt
            if self.oil_temp < PEN_OIL_NORMAL:
                self.oil_temp = PEN_OIL_NORMAL
        else:
            self.oil_temp += PEN_OIL_HEAT_RATE * dt
            if self.oil_temp > 100.0:
                self.oil_temp = 100.0

        # Дополнительный нагрев масла при остановке ГЦН
        if self.gcn_count == 0 or self.gcn_speed < 0.1:
            self.oil_temp += 0.15 * dt
            if self.oil_temp > 100.0:
                self.oil_temp = 100.0

        if self.oil_temp >= PEN_OIL_CRITICAL and not self.oil_damage_done:
            self.oil_damage_done = True
            self.gcn_count = 0
            self.gcn_speed = 0.0
            self.tg7_prot = False
            self.tg8_prot = False
            self.add_log("КРИТИЧЕСКАЯ ПОЛОМКА: Температура масла достигла 80°C! ГЦН, ТГ-7 и ТГ-8 вышли из строя НЕОБРАТИМО!")
            self.station_power = False

        if (self.az5_active or self.az5_locked_out) and self.prot_water and not self.pen_enabled and not self.pen_manual_override:
            self.pen_enabled = True
            self.add_log("АВТОМАТИКА: Включен ПЭН (сработала защита по воде)")

        if self.pen_enabled:
            self.feed_water_flow = self.gcn_count * 400.0 + (self.power / 3200.0) * 200.0
        else:
            self.feed_water_flow = 0.0

        if self.is_exploding or self.steam_explosion_active or self.fuel_melted or self.xenon_pit_active:
            self.explosion_phase = 1
            self.explosion_timer = 0.0
            if self.is_exploding:
                self.end_type = "explosion"
            elif self.steam_explosion_active:
                self.end_type = "steam"
            elif self.fuel_melted:
                self.end_type = "melt"
            elif self.xenon_pit_active:
                self.end_type = "xenon"
            for _ in range(200):
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(100, 500)
                self.explosion_particles.append({
                    'x': WIDTH//2 + random.randint(-150, 150),
                    'y': HEIGHT//2 + random.randint(-150, 150),
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed - 60,
                    'life': random.uniform(0.5, 3.0),
                    'max_life': random.uniform(0.5, 3.0),
                    'size': random.randint(2, 15),
                    'color': (random.randint(200, 255), random.randint(50, 200), random.randint(0, 80)),
                    'type': random.choice(['spark', 'fire', 'smoke', 'fire2'])
                })
            self.explosion_shake_boost = 3.0
            return

        effective_gcn = float(self.gcn_count) if self.station_power else 0.0
        if self.turbine_coasting:
            effective_gcn = max(0.0, effective_gcn - 1.5 * dt)

        if self.cheat_shutdown and self.power < 1.0 and self.rods_pos > 95:
            self.gcn_bearing_temp += (50.0 - self.gcn_bearing_temp) * 0.01 * dt
            if self.gcn_bearing_temp < 50.0:
                self.gcn_bearing_temp = 50.0
            self.shake_intensity = 0.0
            self.flash_intensity = 0.0
            if self.siren_playing:
                stop_sound('alert')
                self.siren_playing = False
            return

        target_gcn = effective_gcn if self.station_power else 0.0
        self.gcn_speed += (target_gcn - self.gcn_speed) * 0.2 * dt
# ========== КОНЕЦ ЧАСТИ 5 ==========
# ========== ЧАСТЬ 6: REACTORSIMULATOR – UPDATE (ФИЗИКА, ЧАСТЬ 2) ==========
        if self.station_power and self.gcn_count > 0:
            cool_rate = BEARING_COOL_SPEED * self.gcn_count
            self.gcn_bearing_temp += (50.0 - self.gcn_bearing_temp) * cool_rate * dt
            if self.gcn_bearing_temp < 50.0:
                self.gcn_bearing_temp = 50.0
        else:
            heat_rate = BEARING_HEAT_RATE_BASE + (8 - self.gcn_count) * BEARING_HEAT_PER_PUMP
            if not self.station_power:
                heat_rate *= 1.5
            self.gcn_bearing_temp += heat_rate * dt

        if self.gcn_bearing_temp >= BEARING_CRITICAL and not self.is_exploding:
            self.is_exploding = True
            self.end_type = "bearing"
            self.explosion_phase = 1
            self.explosion_timer = 0.0
            if 'loop' in sounds: 
                try: sounds['loop'].stop()
                except: pass
            play_sound('explosion')
            self.add_log("КАТАСТРОФА: Заклинивание и взрыв подшипников ГЦН из-за перегрева до 500°C!")
            return

        tg7_factor = 0.5 if self.tg7_prot else 0.0
        tg8_factor = 0.5 if self.tg8_prot else 0.0
        if not self.bru_enabled:
            target_elec = self.power * (tg7_factor + tg8_factor) * 0.3125
            self.elec_power += (target_elec - self.elec_power) * 0.3 * dt
        else:
            self.elec_power = 0.0

        for i in range(10):
            target_lar = self.rods_pos + math.sin(pygame.time.get_ticks()*0.002 + i) * 3.0
            self.lar_positions[i] += (target_lar - self.lar_positions[i]) * 2.0 * dt

        cooling = max(0.05, self.gcn_speed / 8.0)
        if self.gcn_count == 0 or self.gcn_speed < 0.1:
            cooling = 0.05

        bs_effect = self.bs_level / BS_MAX * 100.0
        target_fuel = 270.0 + self.power * FUEL_TEMP_COEFF / math.sqrt(cooling) + bs_effect * 0.2
        self.fuel_temp += (target_fuel - self.fuel_temp) * FUEL_TEMP_SPEED * dt

        # Температура воды
        base_inlet = 280.5
        power_effect = (self.power - 3200.0) / 3200.0 * 20.0
        steam_effect = (self.steam_fraction - 9.3) * 0.5
        flow_effect = 0.0
        if self.feed_water_flow > 0:
            flow_effect = (3200.0 / self.feed_water_flow) * 5.0
        else:
            flow_effect = 50.0
        target_inlet = base_inlet + power_effect + steam_effect + flow_effect
        self.inlet_temp += (target_inlet - self.inlet_temp) * 0.01 * dt
        self.inlet_temp = max(200.0, min(400.0, self.inlet_temp))

        if self.fuel_temp > 2000.0 and not self.fuel_melted:
            self.fuel_melted = True
            self.add_log("КАТАСТРОФА: Температура топлива превысила 2000°C! Активная зона расплавилась.")
            if 'loop' in sounds: 
                try: sounds['loop'].stop()
                except: pass
            play_sound('explosion')
            self.end_type = "melt"
            self.explosion_phase = 1
            self.explosion_timer = 0.0
            return

        if self.az5_active and self.gcn_count == 0 and not self.station_power:
            self.residual_heat_temp += 0.5 * dt
            if self.residual_heat_temp > 2800.0:
                self.fuel_melted = True
                self.add_log("КАТАСТРОФА: Китайский синдром! Активная зона расплавилась и ушла под фундамент.")
                if 'loop' in sounds: 
                    try: sounds['loop'].stop()
                    except: pass
                play_sound('explosion')
                self.end_type = "melt"
                self.explosion_phase = 1
                self.explosion_timer = 0.0
                return

        # ---- ПАРОСОДЕРЖАНИЕ (с учётом БРУ-К) ----
        if self.bru_enabled:
            if self.power <= 1920.0:
                target_steam = 5.0
                self.steam_fraction += (target_steam - self.steam_fraction) * 0.02 * dt
                self.bru_overheat_timer = 0.0
                self.bru_closed_by_protection = False
            else:
                excess = (self.power - 1920.0) / 1920.0
                target_steam = 9.3 + excess * 15.0
                self.steam_fraction += (target_steam - self.steam_fraction) * 0.01 * dt
                self.bru_overheat_timer += dt
                if self.bru_overheat_timer >= BRU_OVERHEAT_TIME and not self.bru_closed_by_protection:
                    self.bru_enabled = False
                    self.bru_open = BRU_CLOSED
                    self.bru_closed_by_protection = True
                    self.add_log("АВАРИЯ: БРУ-К закрыт по защите конденсатора! Пар перегрет!")
        else:
            if self.pen_enabled and self.feed_water_flow > 0:
                target_steam = (self.power / 3200.0) * (1.0 / cooling) * COOLING_BASE
            else:
                target_steam = (self.power / 3200.0) * (1.0 / max(0.01, cooling)) * COOLING_BASE * STEAM_GROWTH_MULTIPLIER

            if self.bru_closed_by_protection and not self.az5_active:
                target_steam = 100.0

            bs_effect_steam = (self.bs_level / BS_MAX) * 10.0
            target_steam += bs_effect_steam
            self.steam_fraction += (target_steam - self.steam_fraction) * STEAM_SPEED * dt
            self.steam_fraction = min(100.0, max(0.0, self.steam_fraction))

        self.bs_pressure = 7.0 + (self.steam_fraction - 9.3) * 0.05 + (self.power - 3200.0) * 0.001 + (self.bs_level / BS_MAX) * 2.0
        self.bs_pressure = max(1.0, min(20.0, self.bs_pressure))

        if self.cheat_steam_ready or self.bs_pressure > PRESSURE_EXPLOSION_LIMIT or self.steam_fraction > STEAM_EXPLOSION_LIMIT:
            if not self.steam_explosion_active:
                self.steam_explosion_active = True
                if 'loop' in sounds: 
                    try: sounds['loop'].stop()
                    except: pass
                play_sound('explosion')
                self.add_log("КАТАСТРОФА: Паровой взрыв барабан-сепаратора и трубопроводов КМПЦ!")
                self.end_type = "steam"
                self.explosion_phase = 1
                self.explosion_timer = 0.0
                return
# ========== КОНЕЦ ЧАСТИ 6 ==========
# ========== ЧАСТЬ 7: REACTORSIMULATOR – UPDATE (ФИЗИКА, ЧАСТЬ 3) ==========
        # ---- КСЕНОН-ЙОД ----
        flux = self.power / 3200.0
        self.iodine += (flux * IODINE_PROD - self.iodine * IODINE_DECAY) * dt
        self.xenon += (self.iodine * XENON_FROM_IODINE - self.xenon * XENON_DECAY - self.xenon * flux * XENON_BURN) * dt
        self.xenon = max(0.0, min(100.0, self.xenon))

        if self.power < 200.0 and self.xenon > 85.0:
            self.xenon_poison_timer += dt
            if self.xenon_poison_timer > 15.0:
                self.xenon_pit_active = True
                self.ozr = 0.0
                self.display_ozr = 0.0
                self.add_log("АВАРИЯ: Ксеноновое отравление (ксеноновая яма)! Реактор заглох намертво.")
                self.end_type = "xenon"
                self.explosion_phase = 1
                self.explosion_timer = 0.0
                return

        if not self.az5_active and not self.az5_locked_out and not self.override_key_turned:
            if (self.power > 3300.0) or \
               (self.prot_water and self.feed_water_flow < 2000.0) or \
               (self.prot_ozr and self.ozr < 15.0 and self.power > 500.0) or \
               (self.gcn_bearing_temp >= 120.0):
                self.az5_active = True
                self.az5_locked_out = True
                self.restart_mode = True
                self.add_log("АВТОМАТИКА: Сработала аварийная защита АЗ-5!")

        rho_rods = (50.0 - self.rods_pos) * RHO_RODS_COEFF
        rho_xe = -(self.xenon - 15.0) * RHO_XE_COEFF
        rho_temp = (555.7 - self.fuel_temp) * RHO_TEMP_COEFF
        rho_steam = (self.steam_fraction - COOLING_BASE) * RHO_STEAM_COEFF

        end_effect = 0.0
        if self.az5_active and self.rods_pos < 100.0:
            old_p = self.rods_pos
            self.rods_pos = min(100.0, self.rods_pos + 12.0 * dt)
            if old_p < 20.0 and self.rods_pos >= 20.0 and not self.prot_ozr:
                end_effect = ROD_END_EFFECT
                if self.turbine_coasting and self.ozr < 15.0:
                    self.chernobyl_explosion = True
                    self.is_exploding = True
                    self.end_type = "explosion"
                    self.explosion_phase = 1
                    self.explosion_timer = 0.0
                    if 'loop' in sounds: 
                        try: sounds['loop'].stop()
                        except: pass
                    play_sound('explosion')
                    self.add_log("КРИТИЧЕСКАЯ АВАРИЯ: Тепловой взрыв активной зоны реактора РБМК-1000!")
                    return
            elif self.rods_pos > 25.0:
                end_effect = -0.05
        elif self.ar_active and not self.az5_locked_out and not self.override_key_turned:
            if self.power < 3190.0 and self.rods_pos > 0.0:
                self.rods_pos = max(0.0, self.rods_pos - 1.5 * dt)
            elif self.power > 3210.0 and self.rods_pos < 100.0:
                self.rods_pos = min(100.0, self.rods_pos + 1.5 * dt)

        total_rho = rho_rods + rho_xe + rho_temp + rho_steam + end_effect
        if self.cheat_boom_ready:
            total_rho += 0.02

        total_rho = max(-0.2, min(0.3, total_rho))
        self.power += total_rho * self.power * (dt / POWER_TIME_CONST)
        self.power = max(0.0, self.power)

        self.ozr = max(0.0, 50.0 - (self.rods_pos * 0.5) - (self.xenon * 0.2))
        self.pyatachok[0] = self.fuel_temp < 1000.0
        self.pyatachok[1] = self.steam_fraction < 80.0
        self.pyatachok[2] = self.gcn_speed > 2.0
        self.pyatachok[3] = self.power < 4000.0

        if (self.power > 12000.0 or self.fuel_temp > 3500.0) and not self.is_exploding:
            self.is_exploding = True
            if 'loop' in sounds: 
                try: sounds['loop'].stop()
                except: pass
            play_sound('explosion')
            self.add_log("КРИТИЧЕСКАЯ АВАРИЯ: Тепловой взрыв активной зоны реактора РБМК-1000!")
            self.end_type = "explosion"
            self.explosion_phase = 1
            self.explosion_timer = 0.0
            return

        # ---- ТРЯСКА И МИГАНИЕ ----
        danger = 0.0
        if self.power > 3300:
            danger = max(danger, (self.power - 3300) / 700.0)
        if self.fuel_temp > 900:
            danger = max(danger, (self.fuel_temp - 900) / 1100.0)
        if self.gcn_bearing_temp > 400:
            danger = max(danger, (self.gcn_bearing_temp - 400) / 100.0)
        if self.steam_fraction > 70:
            danger = max(danger, (self.steam_fraction - 70) / 30.0)
        bs_danger = abs(self.bs_level) / BS_MAX
        danger = max(danger, bs_danger * 0.5)
        if self.bru_overheat_timer > 3.0 and self.bru_enabled:
            danger = max(danger, (self.bru_overheat_timer - 3.0) / BRU_OVERHEAT_TIME * 0.8)
        danger = min(1.0, danger)
        self.shake_intensity = danger * 1.2
        self.flash_intensity = danger * 0.9

        # ---- СИРЕНА ----
        if self.is_alert_active() and self.siren_enabled and self.explosion_phase == 0 and not self.is_exploding:
            if not self.siren_playing:
                play_sound('alert')
                self.siren_playing = True
        else:
            if self.siren_playing:
                stop_sound('alert')
                self.siren_playing = False

        # ---- ТРИГГЕР СКРЫТОЙ ПОЛОМКИ ----
        if not self.hidden_mode_active and not self.cheat_hidden:
            if self.power > 5000.0 and not self.tg7_prot and not self.tg8_prot and self.az5_active:
                self.hidden_mode_active = True
                self.display_frozen = True
                self.hidden_timer = 0.0
                self.hidden_power = self.power
                self.hidden_fuel_temp = self.fuel_temp
                self.hidden_steam_fraction = self.steam_fraction
                self.frozen_power = self.power
                self.frozen_elec_power = self.elec_power
                self.frozen_fuel_temp = self.fuel_temp
                self.frozen_steam_fraction = self.steam_fraction
                self.frozen_xenon = self.xenon
                self.frozen_ozr = self.ozr
                self.frozen_bs_level = self.bs_level
                self.frozen_gcn_bearing_temp = self.gcn_bearing_temp
                self.frozen_oil_temp = self.oil_temp
                self.add_log("АЗ-5 активирована, стержни идут вниз.")
                self.event_log.append("СКРЫТО: Режим ложной стабильности активирован.")

        # ---- МИССИИ ----
        if self.mission_mode and not self.console_visible:
            self.check_mission()

    # ---- ВСПОМОГАТЕЛЬНЫЙ МЕТОД ----
    def is_alert_active(self):
        oil_alarm = self.oil_temp >= PEN_OIL_CRITICAL
        gcn_off = (self.gcn_count == 0)
        bs_alarm = abs(self.bs_level) > 800.0
        bru_alarm = self.bru_overheat_timer > 4.0 and self.bru_enabled
        return (self.power > 3300.0 or
                self.power_vel > 200.0 or
                self.gcn_count < 4 or
                self.bs_pressure > 8.5 or
                self.ozr < 15.0 or
                oil_alarm or
                gcn_off or
                (not self.pen_enabled and self.oil_temp > 60.0) or
                bs_alarm or
                bru_alarm)
# ========== КОНЕЦ ЧАСТИ 7 ==========
# ========== ЧАСТЬ 8: ФУНКЦИИ РИСОВАНИЯ ==========
def draw_soviet_switch(cx, cy, label, state, angle):
    pygame.draw.rect(screen, COLOR_PANEL_DARK, (cx - 40, cy - 25, 80, 50), border_radius=3)
    pygame.draw.rect(screen, COLOR_FRAME, (cx - 40, cy - 25, 80, 50), 2, border_radius=3)
    pygame.draw.circle(screen, (40, 45, 40), (cx, cy - 5), 15)
    pygame.draw.circle(screen, (20, 20, 20), (cx, cy - 5), 15, 2)
    rad = math.radians(angle)
    dx = math.cos(rad) * 11
    dy = math.sin(rad) * 11
    pygame.draw.line(screen, (220, 220, 210), (cx - dx, cy - 5 - dy), (cx + dx, cy - 5 + dy), 4)
    txt = font_bold.render(label, True, COLOR_TEXT_DARK)
    screen.blit(txt, (cx - txt.get_width()//2, cy + 12))

def draw_soviet_star(surface, cx, cy, radius, color):
    points = []
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        r = radius if i % 2 == 0 else radius * 0.382
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(surface, color, points)

def draw_gas_mask(surface, cx, cy, size):
    pygame.draw.circle(surface, (80, 80, 80), (cx, cy), size)
    pygame.draw.circle(surface, (100, 100, 100), (cx, cy), size, 2)
    pygame.draw.circle(surface, (150, 200, 220, 100), (cx, cy), size//2)
    pygame.draw.rect(surface, (60, 60, 60), (cx - size//4, cy + size//2 - 5, size//2, size//2))
    pygame.draw.rect(surface, (40, 40, 40), (cx - size//4, cy + size//2 - 5, size//2, size//2), 2)
    pygame.draw.circle(surface, (200, 200, 200), (cx - size//3, cy - size//6), size//5)
    pygame.draw.circle(surface, (200, 200, 200), (cx + size//3, cy - size//6), size//5)
    pygame.draw.circle(surface, (50, 50, 50), (cx - size//3, cy - size//6), size//8)
    pygame.draw.circle(surface, (50, 50, 50), (cx + size//3, cy - size//6), size//8)

def draw_soviet_button(rect, text, hover, is_menu=False):
    scale = 1.0 + hover * 0.05
    new_w = int(rect.width * scale)
    new_h = int(rect.height * scale)
    new_x = rect.centerx - new_w//2
    new_y = rect.centery - new_h//2
    new_rect = pygame.Rect(new_x, new_y, new_w, new_h)
    col = (140 + int(hover * 40), 50 + int(hover * 30), 50 + int(hover * 30))
    pygame.draw.rect(screen, col, new_rect, border_radius=6)
    pygame.draw.rect(screen, (230, 190, 60), new_rect, max(2, int(2 + hover * 2)), border_radius=6)
    font_size = 36 + int(hover * 6)
    if is_menu:
        font_size = 42 + int(hover * 8)
    fnt = pygame.font.Font(None, font_size); fnt.set_bold(True)
    txt = fnt.render(text, True, (255, 240 + int(hover*15), 180 + int(hover*75)))
    screen.blit(txt, (new_rect.centerx - txt.get_width()//2, new_rect.centery - txt.get_height()//2))
    return new_rect

def draw_magnetola_button(rect, text, hover):
    col = (60 + hover*30, 65 + hover*30, 60 + hover*30)
    pygame.draw.rect(screen, col, rect, border_radius=4)
    pygame.draw.rect(screen, (100, 110, 100), rect, 1, border_radius=4)
    txt = font_bold.render(text, True, (200, 220, 200))
    screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

# ---- ОТРИСОВКА КРУГЛОГО ДАТЧИКА БС ----
def draw_bs_gauge(cx, cy, radius, value, min_val, max_val):
    pygame.draw.circle(screen, (40, 45, 40), (cx, cy), radius)
    pygame.draw.circle(screen, (80, 85, 80), (cx, cy), radius, 2)
    for i in range(-5, 6):
        angle = math.radians(90 + i * 35)
        x1 = cx + (radius - 12) * math.cos(angle)
        y1 = cy - (radius - 12) * math.sin(angle)
        x2 = cx + (radius - 4) * math.cos(angle)
        y2 = cy - (radius - 4) * math.sin(angle)
        if i % 2 == 0:
            pygame.draw.line(screen, (200, 200, 200), (x1, y1), (x2, y2), 2)
            val_text = str(i * 300)
            txt = font_small.render(val_text, True, (200, 200, 200))
            tx = cx + (radius - 20) * math.cos(angle) - txt.get_width()//2
            ty = cy - (radius - 20) * math.sin(angle) - txt.get_height()//2
            screen.blit(txt, (tx, ty))
        else:
            pygame.draw.line(screen, (150, 150, 150), (x1, y1), (x2, y2), 1)
    pygame.draw.circle(screen, (200, 200, 200), (cx, cy), 3)
    norm_val = (value - min_val) / (max_val - min_val)
    angle_arrow = math.radians(norm_val * 360 - 90)
    arrow_len = radius - 8
    end_x = cx + arrow_len * math.cos(angle_arrow)
    end_y = cy - arrow_len * math.sin(angle_arrow)
    pygame.draw.line(screen, (255, 40, 40), (cx, cy), (end_x, end_y), 3)
    pygame.draw.circle(screen, (255, 40, 40), (int(end_x), int(end_y)), 4)
    val_txt = font_bold.render(f"{int(value)} мм", True, (255, 255, 200))
    screen.blit(val_txt, (cx - val_txt.get_width()//2, cy + radius + 10))
# ========== КОНЕЦ ЧАСТИ 8 ==========
# ========== ЧАСТЬ 9: ВЫБОР МУЗЫКИ ==========
def choose_music():
    browser_running = True
    current_dir = "/storage/emulated/0" if os.path.exists("/storage/emulated/0") else os.path.abspath(os.getcwd())
    scroll = 0
    font_fb = pygame.font.Font(None, 32)
    while browser_running:
        try:
            items = [".."] + sorted(os.listdir(current_dir))
        except:
            items = [".."]
        display_items = []
        for item in items:
            if item == "..": 
                display_items.append(item)
            else:
                path = os.path.join(current_dir, item)
                if os.path.isdir(path): 
                    display_items.append(item + "/")
                elif item.lower().endswith(('.mp3', '.wav', '.ogg')): 
                    display_items.append(item)
        screen.fill((30, 40, 30))
        pygame.draw.rect(screen, (75, 85, 78), (10, 10, WIDTH-20, HEIGHT-20), 4, border_radius=5)
        title = font_fb.render(f"МАГНИТОЛА: ВЫБОР ФАЙЛА - {current_dir}", True, (200, 220, 200))
        screen.blit(title, (30, 30))
        close_btn = pygame.Rect(WIDTH - 160, 25, 130, 40)
        pygame.draw.rect(screen, (200, 50, 50), close_btn, border_radius=5)
        pygame.draw.rect(screen, (255, 200, 50), close_btn, 2, border_radius=5)
        c_txt = font_fb.render("ЗАКРЫТЬ", True, (255, 255, 255))
        screen.blit(c_txt, (close_btn.centerx - c_txt.get_width()//2, close_btn.centery - c_txt.get_height()//2))
        scroll_up_btn = pygame.Rect(WIDTH - 60, 90, 40, 30)
        scroll_down_btn = pygame.Rect(WIDTH - 60, HEIGHT - 100, 40, 30)
        pygame.draw.rect(screen, (80,80,80), scroll_up_btn)
        pygame.draw.rect(screen, (80,80,80), scroll_down_btn)
        up_txt = font_fb.render("▲", True, (255,255,255))
        down_txt = font_fb.render("▼", True, (255,255,255))
        screen.blit(up_txt, (scroll_up_btn.centerx - up_txt.get_width()//2, scroll_up_btn.centery - up_txt.get_height()//2))
        screen.blit(down_txt, (scroll_down_btn.centerx - down_txt.get_width()//2, scroll_down_btn.centery - down_txt.get_height()//2))
        scrollbar_rect = pygame.Rect(WIDTH - 30, 90, 20, HEIGHT - 200)
        pygame.draw.rect(screen, (60,60,60), scrollbar_rect)
        max_visible = (HEIGHT - 100) // 40
        if len(display_items) > max_visible:
            scroll_pos = scroll / (len(display_items) - max_visible)
            thumb_h = max(20, scrollbar_rect.height * (max_visible / len(display_items)))
            thumb_y = scrollbar_rect.y + (scrollbar_rect.height - thumb_h) * scroll_pos
            thumb_rect = pygame.Rect(scrollbar_rect.x, thumb_y, scrollbar_rect.width, thumb_h)
            pygame.draw.rect(screen, (150,150,150), thumb_rect)
        mx, my = pygame.mouse.get_pos()
        click = False
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: return []
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 4: scroll = max(0, scroll - 3)
                if ev.button == 5: scroll = min(max(0, len(display_items) - max_visible), scroll + 3)
                if ev.button == 1:
                    click = True
                    if close_btn.collidepoint(ev.pos): return []
                    if scrollbar_rect.collidepoint(ev.pos):
                        if ev.pos[1] < thumb_rect.y:
                            scroll = max(0, scroll - max_visible//2)
                        elif ev.pos[1] > thumb_rect.y + thumb_rect.height:
                            scroll = min(max(0, len(display_items) - max_visible), scroll + max_visible//2)
                    if scroll_up_btn.collidepoint(ev.pos):
                        scroll = max(0, scroll - 2)
                    if scroll_down_btn.collidepoint(ev.pos):
                        scroll = min(max(0, len(display_items) - max_visible), scroll + 2)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: return []
        for i in range(min(max_visible, len(display_items) - scroll)):
            idx = scroll + i
            if idx >= len(display_items): break
            item_text = display_items[idx]
            rect_y = 90 + i * 40
            item_rect = pygame.Rect(30, rect_y, WIDTH - 90, 35)
            hover = item_rect.collidepoint(mx, my)
            if hover: pygame.draw.rect(screen, (60, 70, 60), item_rect, border_radius=3)
            col = (220, 200, 100) if item_text.endswith("/") or item_text == ".." else (150, 220, 255)
            screen.blit(font_fb.render(item_text, True, col), (40, rect_y + 5))
            if click and hover:
                play_sound('click')
                if item_text == "..":
                    current_dir = os.path.dirname(current_dir)
                    scroll = 0
                elif item_text.endswith("/"):
                    current_dir = os.path.join(current_dir, item_text[:-1])
                    scroll = 0
                else:
                    return [os.path.join(current_dir, item_text)]
        pygame.display.flip()
        clock.tick(30)
# ========== КОНЕЦ ЧАСТИ 9 ==========
# ========== ЧАСТЬ 10: ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
reactor = ReactorSimulator()

game_state = "MAIN_MENU"
trans_alpha = 0.0

mag_is_open = False
mag_anim_val = 0.0
playlist = []
current_track = -1
music_vol = 0.5
pygame.mixer.music.set_volume(music_vol)

hovers = {"play": 0.0, "exit": 0.0, "restart": 0.0, "mag_icon": 0.0, "mag_center": 0.0,
          "v_up": 0.0, "v_dn": 0.0, "t_nxt": 0.0, "t_prv": 0.0, "about": 0.0, "scenarios": 0.0}

btn_play = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 130, 300, 60)
btn_about = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 50, 300, 60)
btn_scenarios = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 30, 300, 60)   # новая кнопка
btn_exit = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 110, 300, 60)

rect_restart = pygame.Rect(WIDTH//2 - 150, HEIGHT - 100, 300, 60)

mag_icon_rect = pygame.Rect(WIDTH - 50, 15, 35, 35)

about_open = False
about_rect = pygame.Rect(WIDTH//2 - 300, HEIGHT//2 - 150, 600, 300)
about_close_rect = pygame.Rect(about_rect.right - 40, about_rect.top + 10, 30, 30)

# ---- ОКНО СЦЕНАРИЕВ ----
scenarios_rect = pygame.Rect(WIDTH//2 - 350, HEIGHT//2 - 250, 700, 500)
scenarios_close_rect = pygame.Rect(scenarios_rect.right - 40, scenarios_rect.top + 10, 30, 30)
scenario_btn_1_1 = pygame.Rect(scenarios_rect.x + 50, scenarios_rect.y + 100, 280, 40)
scenario_btn_1_2 = pygame.Rect(scenarios_rect.x + 370, scenarios_rect.y + 100, 280, 40)
scenario_btn_2_1 = pygame.Rect(scenarios_rect.x + 50, scenarios_rect.y + 210, 280, 40)
scenario_btn_2_2 = pygame.Rect(scenarios_rect.x + 370, scenarios_rect.y + 210, 280, 40)
scenario_btn_3_1 = pygame.Rect(scenarios_rect.x + 50, scenarios_rect.y + 320, 280, 40)
scenario_btn_3_2 = pygame.Rect(scenarios_rect.x + 370, scenarios_rect.y + 320, 280, 40)

menu_open = False
rect_menu_btn = pygame.Rect(20, 20, 34, 34)
menu_w, menu_h = 420, 660
menu_rect = pygame.Rect(WIDTH//2 - menu_w//2, HEIGHT//2 - menu_h//2, menu_w, menu_h)
rect_close = pygame.Rect(menu_rect.right - 45, menu_rect.top + 15, 30, 30)

btn_boom = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 70, 360, 38)
btn_steam = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 115, 360, 38)
btn_black = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 160, 360, 38)
btn_melt = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 205, 360, 38)
btn_xenon = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 250, 360, 38)
btn_bearing = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 295, 360, 38)
btn_shutdown = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 340, 360, 38)
btn_startup = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 385, 360, 38)
btn_hidden = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 430, 360, 38)
btn_norm = pygame.Rect(menu_rect.centerx - 180, menu_rect.top + 475, 360, 42)

rect_suz_up = pygame.Rect(25, 655, 140, 40)
rect_suz_down = pygame.Rect(175, 655, 140, 40)
rect_scala = pygame.Rect(25, 490, 240, 32)

rect_gcn_plus = pygame.Rect(1185, 265, 35, 28)
rect_gcn_minus = pygame.Rect(1145, 265, 35, 28)

rect_az5_reset = pygame.Rect(870, 655, 180, 40)
rect_turbine_coast = pygame.Rect(1070, 655, 180, 40)
rect_siren_off = pygame.Rect(720, 658, 140, 32)

rect_pen_toggle = pygame.Rect(1000 - 40, 455 - 25, 80, 50)
rect_bru_toggle = pygame.Rect(1090 - 40, 455 - 25, 80, 50)
rect_dg_toggle = pygame.Rect(1170 - 40, 455 - 25, 80, 50)

bs_cx, bs_cy = 1180, 155
bs_radius = 50
rect_bs_plus = pygame.Rect(bs_cx + bs_radius + 10, bs_cy - 15, 30, 25)
rect_bs_minus = pygame.Rect(bs_cx + bs_radius + 10, bs_cy + 15, 30, 25)
rect_bs_auto = pygame.Rect(890 - 40, 380 - 25, 80, 50)

rect_override = pygame.Rect(1150, 495, 100, 60)
rect_az5_button = pygame.Rect(1150, 575, 100, 60)

filter_rects = {
    "ALL": pygame.Rect(25, 462, 70, 26),
    "RODS": pygame.Rect(100, 462, 70, 26),
    "POWER": pygame.Rect(175, 462, 70, 26),
    "AZ": pygame.Rect(250, 462, 70, 26)
}

btn_arrow_u = pygame.Rect(605, 125, 32, 28)
btn_arrow_d = pygame.Rect(605, 185, 32, 28)
btn_arrow_l = pygame.Rect(570, 155, 32, 28)
btn_arrow_r = pygame.Rect(640, 155, 32, 28)

switch_zones = {
    "tg7": (740, 820, 355, 405),
    "tg8": (740, 820, 430, 480),
    "bs_auto": (890, 890, 355, 405),
    "ar": (850, 930, 430, 480),
    "p_water": (960, 1040, 355, 405),
    "p_ozr": (960, 1040, 430, 480),
    "gcn": (1050, 1130, 355, 405),
    "pen": (960, 1040, 430, 480),
    "bru": (1050, 1130, 430, 480),
    "dg": (1130, 1210, 430, 480)
}

running = True
# ========== КОНЕЦ ЧАСТИ 10 ==========
# ========== ЧАСТЬ 11: ОСНОВНОЙ ЦИКЛ – ОБРАБОТКА СОБЫТИЙ ==========
while running:
    dt = clock.tick(60) / 1000.0
    current_time = pygame.time.get_ticks()
    mx, my = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()[0]
    gameover_active = (reactor.explosion_phase > 0 or reactor.console_visible)

    reactor.bs_manual_plus = rect_bs_plus.collidepoint(mx, my) and click and not reactor.bs_auto
    reactor.bs_manual_minus = rect_bs_minus.collidepoint(mx, my) and click and not reactor.bs_auto

    target_mag = 1.0 if mag_is_open else 0.0
    mag_anim_val += (target_mag - mag_anim_val) * 8.0 * dt
    mag_x = WIDTH - int(mag_anim_val * 310) + 10
    mag_panel = pygame.Rect(mag_x, 60, 290, 80)
    mag_btn_vol_up = pygame.Rect(mag_panel.x + 10, mag_panel.y + 10, 30, 25)
    mag_btn_vol_dn = pygame.Rect(mag_panel.x + 10, mag_panel.y + 45, 30, 25)
    mag_btn_prv = pygame.Rect(mag_panel.right - 40, mag_panel.y + 10, 30, 25)
    mag_btn_nxt = pygame.Rect(mag_panel.right - 40, mag_panel.y + 45, 30, 25)
    mag_btn_mid = pygame.Rect(mag_panel.x + 50, mag_panel.y + 10, 190, 60)

    def update_h(k, r):
        hovers[k] = min(1.0, hovers[k] + 5*dt) if r.collidepoint(mx, my) else max(0.0, hovers[k] - 5*dt)
    
    update_h("play", btn_play)
    update_h("exit", btn_exit)
    update_h("about", btn_about)
    update_h("scenarios", btn_scenarios)
    update_h("restart", rect_restart)
    update_h("mag_icon", mag_icon_rect)
    update_h("mag_center", mag_btn_mid)
    update_h("v_up", mag_btn_vol_up)
    update_h("v_dn", mag_btn_vol_dn)
    update_h("t_nxt", mag_btn_nxt)
    update_h("t_prv", mag_btn_prv)

    if game_state == "TRANS_TO_GAME":
        trans_alpha += 400 * dt
        if trans_alpha >= 255: game_state = "GAME"; trans_alpha = 255
    elif game_state == "TRANS_TO_MENU":
        trans_alpha += 400 * dt
        if trans_alpha >= 255: 
            game_state = "MAIN_MENU"
            reactor = ReactorSimulator()
            evac_started = False
            if 'loop' in sounds: 
                try: sounds['loop'].play(-1)
                except: pass
            trans_alpha = 255
    else:
        trans_alpha = max(0.0, trans_alpha - 400 * dt)

    if click and game_state == "GAME" and not menu_open and not reactor.az5_active and not reactor.ar_active and not reactor.is_exploding and not reactor.az5_locked_out:
        if rect_suz_up.collidepoint(mx, my):
            if reactor.cheat_shutdown and reactor.power < 1.0:
                reactor.rods_pos = max(0.0, reactor.rods_pos - 6.0 * dt)
                if reactor.rods_pos < 50 and reactor.gcn_count >= 4:
                    reactor.cheat_shutdown = False
                    reactor.add_log("ПУСК: Стержни подняты, ГЦН работают. Реактор выходит на мощность.")
            else:
                reactor.rods_pos = max(0.0, reactor.rods_pos - 6.0 * dt)
        elif rect_suz_down.collidepoint(mx, my):
            reactor.rods_pos = min(100.0, reactor.rods_pos + 6.0 * dt)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
            
        if event.type == pygame.KEYDOWN:
            if game_state == "GAME" and not menu_open and not about_open:
                gx, gy = reactor.selected_grid_pos
                if event.key == pygame.K_UP: reactor.selected_grid_pos = (gx, max(0, gy - 1))
                elif event.key == pygame.K_DOWN: reactor.selected_grid_pos = (gx, min(26, gy + 1))
                elif event.key == pygame.K_LEFT: reactor.selected_grid_pos = (max(0, gx - 1), gy)
                elif event.key == pygame.K_RIGHT: reactor.selected_grid_pos = (min(26, gx + 1), gy)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if mag_icon_rect.collidepoint(mx, my):
                mag_is_open = not mag_is_open; play_sound('click'); continue
            if mag_is_open:
                if mag_btn_vol_up.collidepoint(mx, my): music_vol = min(1.0, music_vol + 0.1); pygame.mixer.music.set_volume(music_vol); play_sound('click'); continue
                if mag_btn_vol_dn.collidepoint(mx, my): music_vol = max(0.0, music_vol - 0.1); pygame.mixer.music.set_volume(music_vol); play_sound('click'); continue
                if mag_btn_nxt.collidepoint(mx, my) and playlist: current_track = (current_track + 1) % len(playlist); pygame.mixer.music.load(playlist[current_track]); pygame.mixer.music.play(); play_sound('click'); continue
                if mag_btn_prv.collidepoint(mx, my) and playlist: current_track = (current_track - 1) % len(playlist); pygame.mixer.music.load(playlist[current_track]); pygame.mixer.music.play(); play_sound('click'); continue
                if mag_btn_mid.collidepoint(mx, my):
                    play_sound('click')
                    new_t = choose_music()
                    if new_t:
                        playlist = list(new_t); current_track = 0
                        pygame.mixer.music.load(playlist[0]); pygame.mixer.music.play()
                    continue

            if game_state == "MAIN_MENU" and trans_alpha == 0:
                if btn_play.collidepoint(mx, my):
                    play_sound('click')
                    game_state = "TRANS_TO_GAME"
                elif btn_about.collidepoint(mx, my):
                    play_sound('click')
                    about_open = True
                elif btn_scenarios.collidepoint(mx, my):
                    play_sound('click')
                    game_state = "SCENARIOS"
                elif btn_exit.collidepoint(mx, my):
                    play_sound('click')
                    running = False
                continue

            if about_open:
                if about_close_rect.collidepoint(mx, my):
                    about_open = False; play_sound('click')
                continue

            # ---- ОБРАБОТКА СЦЕНАРИЕВ ----
            if game_state == "SCENARIOS":
                if scenarios_close_rect.collidepoint(mx, my):
                    play_sound('click')
                    game_state = "MAIN_MENU"
                    continue
                if scenario_btn_1_1.collidepoint(mx, my):
                    play_sound('click')
                    reactor.set_mission(1)
                    game_state = "TRANS_TO_GAME"
                elif scenario_btn_1_2.collidepoint(mx, my):
                    play_sound('click')
                    reactor.set_mission(2)
                    game_state = "TRANS_TO_GAME"
                elif scenario_btn_2_1.collidepoint(mx, my):
                    play_sound('click')
                    reactor.set_mission(3)
                    game_state = "TRANS_TO_GAME"
                elif scenario_btn_2_2.collidepoint(mx, my):
                    play_sound('click')
                    reactor.set_mission(4)
                    game_state = "TRANS_TO_GAME"
                elif scenario_btn_3_1.collidepoint(mx, my):
                    play_sound('click')
                    reactor.set_mission(5)
                    game_state = "TRANS_TO_GAME"
                elif scenario_btn_3_2.collidepoint(mx, my):
                    play_sound('click')
                    reactor.set_mission(6)
                    game_state = "TRANS_TO_GAME"
                continue

            if gameover_active and rect_restart.collidepoint(mx, my):
                play_sound('click')
                game_state = "TRANS_TO_MENU"
                continue

            if game_state == "GAME" and not gameover_active:
                if menu_open:
                    if rect_close.collidepoint(mx, my): menu_open = False
                    elif btn_boom.collidepoint(mx, my): reactor.set_boom_prep(); menu_open = False
                    elif btn_steam.collidepoint(mx, my): reactor.set_steam_prep(); menu_open = False
                    elif btn_black.collidepoint(mx, my): reactor.set_blackout_prep(); menu_open = False
                    elif btn_melt.collidepoint(mx, my): reactor.set_melt_prep(); menu_open = False
                    elif btn_xenon.collidepoint(mx, my): reactor.set_xenon_prep(); menu_open = False
                    elif btn_bearing.collidepoint(mx, my): reactor.set_bearing_prep(); menu_open = False
                    elif btn_shutdown.collidepoint(mx, my): reactor.set_shutdown_prep(); menu_open = False
                    elif btn_startup.collidepoint(mx, my): reactor.set_startup_prep(); menu_open = False
                    elif btn_hidden.collidepoint(mx, my): reactor.set_hidden_prep(); menu_open = False
                    elif btn_norm.collidepoint(mx, my): reactor.reset_normal(); menu_open = False
                    continue

                play_sound('click')
                if rect_menu_btn.collidepoint(mx, my): menu_open = True; continue

                # ---- БС ----
                if rect_bs_auto.collidepoint(mx, my):
                    reactor.bs_auto = not reactor.bs_auto
                    reactor.add_log(f"АВТОМАТИКА БС: {'ВКЛ' if reactor.bs_auto else 'ВЫКЛ'}")
                    play_sound('click')
                    continue
                if rect_bs_plus.collidepoint(mx, my) and not reactor.bs_auto:
                    reactor.bs_level += BS_MANUAL_SPEED * 0.1
                    reactor.bs_level = min(BS_MAX, reactor.bs_level)
                    play_sound('click')
                    continue
                if rect_bs_minus.collidepoint(mx, my) and not reactor.bs_auto:
                    reactor.bs_level -= BS_MANUAL_SPEED * 0.1
                    reactor.bs_level = max(BS_MIN, reactor.bs_level)
                    play_sound('click')
                    continue

                # ---- ПЭН, БРУ-К, ДГ ----
                if rect_pen_toggle.collidepoint(mx, my):
                    reactor.pen_enabled = not reactor.pen_enabled
                    reactor.pen_manual_override = not reactor.pen_enabled
                    play_sound('click')
                    reactor.add_log(f"ПЭН: {'ВКЛЮЧЕН' if reactor.pen_enabled else 'ВЫКЛЮЧЕН'}")
                    continue

                if rect_bru_toggle.collidepoint(mx, my):
                    if not reactor.tg7_prot or not reactor.tg8_prot:
                        reactor.bru_enabled = not reactor.bru_enabled
                        if reactor.bru_enabled:
                            reactor.add_log("БРУ-К ВКЛЮЧЕН")
                        else:
                            reactor.bru_enabled = False
                            reactor.bru_open = BRU_CLOSED
                            reactor.bru_overheat_timer = 0.0
                            reactor.bru_closed_by_protection = False
                            reactor.add_log("БРУ-К ВЫКЛЮЧЕН")
                        play_sound('click')
                    else:
                        reactor.add_log("ОШИБКА: Для включения БРУ-К отключите ТГ-7 и ТГ-8")
                    continue

                if rect_dg_toggle.collidepoint(mx, my):
                    if reactor.dg_fuel <= 0:
                        reactor.add_log("ОШИБКА: Дизель закончился, ДГ не может быть включён")
                    else:
                        reactor.dg_enabled = not reactor.dg_enabled
                        if reactor.dg_enabled:
                            reactor.add_log("Дизель-генератор: запуск... (45 сек)")
                            reactor.dg_start_timer = 0.0
                        else:
                            reactor.dg_running = False
                            reactor.dg_start_timer = 0.0
                            reactor.add_log("Дизель-генератор выключен")
                        play_sound('click')
                    continue

                if rect_az5_reset.collidepoint(mx, my): reactor.az5_reset_pressed = True; reactor.restart_reactor(); continue
                if rect_turbine_coast.collidepoint(mx, my): reactor.turbine_coasting = not reactor.turbine_coasting; reactor.add_log(f"ТУРБИНА: Выбег ТГ {'активирован' if reactor.turbine_coasting else 'отключен'}"); continue

                if rect_siren_off.collidepoint(mx, my):
                    reactor.siren_enabled = not reactor.siren_enabled
                    if not reactor.siren_enabled:
                        stop_sound('alert')
                        reactor.siren_playing = False
                    else:
                        if reactor.is_alert_active():
                            play_sound('alert')
                            reactor.siren_playing = True
                    play_sound('click')
                    reactor.add_log(f"СИРЕНА: {'ВКЛ' if reactor.siren_enabled else 'ВЫКЛ'}")
                    continue

                for f_name, f_rect in filter_rects.items():
                    if f_rect.collidepoint(mx, my): reactor.filter_mode = f_name; reactor.add_log(f"Мнемосхема: установлен фильтр -> {f_name}")

                gx, gy = reactor.selected_grid_pos
                if btn_arrow_u.collidepoint(mx, my): reactor.selected_grid_pos = (gx, max(0, gy - 1))
                elif btn_arrow_d.collidepoint(mx, my): reactor.selected_grid_pos = (gx, min(26, gy + 1))
                elif btn_arrow_l.collidepoint(mx, my): reactor.selected_grid_pos = (max(0, gx - 1), gy)
                elif btn_arrow_r.collidepoint(mx, my): reactor.selected_grid_pos = (min(26, gx + 1), gy)

                for ch in reactor.core_map:
                    if pygame.Rect(ch["x"], ch["y"], 11, 11).collidepoint(mx, my): reactor.selected_grid_pos = (ch["grid_x"], ch["grid_y"])
                    
                if rect_gcn_plus.collidepoint(mx, my): reactor.gcn_count = min(8, reactor.gcn_count + 1); reactor.add_log(f"ГЦН: Ручное увеличение до {reactor.gcn_count}/8")
                elif rect_gcn_minus.collidepoint(mx, my): reactor.gcn_count = max(0, reactor.gcn_count - 1); reactor.add_log(f"ГЦН: Ручное снижение до {reactor.gcn_count}/8")

                if rect_override.collidepoint(mx, my) and not reactor.is_exploding:
                    if not reactor.override_cap_open: reactor.override_cap_open = True; reactor.add_log("БЛОК. АЗ-5: Защитная крышка открыта")
                    elif not reactor.override_key_inserted: reactor.override_key_inserted = True; reactor.add_log("БЛОК. АЗ-5: Ключ вставлен")
                    elif not reactor.override_key_turned: reactor.override_key_turned = True; reactor.az5_active = False; reactor.az5_locked_out = False; reactor.restart_mode = False; reactor.add_log("БЛОК. АЗ-5: Ключ повернут! Автоматика АЗ-5 полностью деактивирована.")
                    
                if rect_az5_button.collidepoint(mx, my) and not reactor.is_exploding:
                    if not reactor.az5_cap_open: reactor.az5_cap_open = True; reactor.add_log("АЗ-5: Защитная крышка открыта")
                    else: 
                        reactor.az5_active = not reactor.az5_active; reactor.az5_locked_out = False
                        if reactor.az5_active: reactor.add_log("АЗ-5: Нажата аварийная защита вручную!")
                        else: reactor.add_log("АЗ-5: Отжата вручную")

                if rect_scala.collidepoint(mx, my) and reactor.scala_state == "IDLE":
                    if reactor.display_frozen:
                        reactor.add_log("ОШИБКА: Нет связи с датчиками СКАЛА")
                    else:
                        reactor.scala_state = "CALCULATING"
                        reactor.scala_timer = 0.0
                        reactor.add_log("СКАЛА: Запрошен расчет ОЗР...")

                # ---- ПЕРЕКЛЮЧАТЕЛИ ----
                if 740 <= mx <= 820:
                    if 355 <= my <= 405: reactor.tg7_prot = not reactor.tg7_prot; reactor.add_log(f"Защита ТГ-7: {'Вкл' if reactor.tg7_prot else 'Выкл'}")
                    elif 430 <= my <= 480: reactor.tg8_prot = not reactor.tg8_prot; reactor.add_log(f"Защита ТГ-8: {'Вкл' if reactor.tg8_prot else 'Выкл'}")
                elif 850 <= mx <= 930:
                    if 355 <= my <= 405: reactor.bs_auto = not reactor.bs_auto; reactor.add_log(f"АВТОМАТИКА БС: {'ВКЛ' if reactor.bs_auto else 'ВЫКЛ'}")
                    elif 430 <= my <= 480: reactor.ar_active = not reactor.ar_active; reactor.add_log(f"Регулятор АР: {'Вкл' if reactor.ar_active else 'Выкл'}")
                elif 960 <= mx <= 1040:
                    if 355 <= my <= 405: reactor.prot_water = not reactor.prot_water; reactor.add_log(f"Защита по воде: {'Вкл' if reactor.prot_water else 'Выкл'}")
                    elif 430 <= my <= 480: reactor.pen_enabled = not reactor.pen_enabled; reactor.pen_manual_override = not reactor.pen_enabled; reactor.add_log(f"ПЭН: {'ВКЛЮЧЕН' if reactor.pen_enabled else 'ВЫКЛЮЧЕН'}")
                elif 1050 <= mx <= 1130:
                    if 355 <= my <= 405: reactor.gcn_count = (reactor.gcn_count + 1) % 9; reactor.add_log(f"ГЦН: Переключение на {reactor.gcn_count}/8")
                    elif 430 <= my <= 480: 
                        if not reactor.tg7_prot or not reactor.tg8_prot:
                            reactor.bru_enabled = not reactor.bru_enabled
                            if reactor.bru_enabled:
                                reactor.add_log("БРУ-К ВКЛЮЧЕН")
                            else:
                                reactor.bru_enabled = False
                                reactor.bru_open = BRU_CLOSED
                                reactor.bru_overheat_timer = 0.0
                                reactor.bru_closed_by_protection = False
                                reactor.add_log("БРУ-К ВЫКЛЮЧЕН")
                        else:
                            reactor.add_log("ОШИБКА: Для включения БРУ-К отключите ТГ-7 и ТГ-8")
                elif 1130 <= mx <= 1210 and 430 <= my <= 480:
                    if reactor.dg_fuel <= 0:
                        reactor.add_log("ОШИБКА: Дизель закончился, ДГ не может быть включён")
                    else:
                        reactor.dg_enabled = not reactor.dg_enabled
                        if reactor.dg_enabled:
                            reactor.add_log("Дизель-генератор: запуск... (45 сек)")
                            reactor.dg_start_timer = 0.0
                        else:
                            reactor.dg_running = False
                            reactor.dg_start_timer = 0.0
                            reactor.add_log("Дизель-генератор выключен")
# ========== КОНЕЦ ЧАСТИ 11 ==========
# ========== ЧАСТЬ 12a: МЕНЮ, МНЕМОСХЕМА, ПАНЕЛИ (С ИСПРАВЛЕННЫМИ БАГАМИ) ==========
    if game_state == "GAME" and not gameover_active:
        reactor.update(dt)

    if game_state in ["MAIN_MENU", "TRANS_TO_GAME"]:
        screen.blit(menu_bg_img, (0, 0))
        title_txt = font_title.render("СИМУЛЯТОР РБМК-1000", True, (255, 215, 0))
        screen.blit(title_txt, (WIDTH//2 - title_txt.get_width()//2 - 40, 100))
        draw_soviet_star(screen, WIDTH//2 + title_txt.get_width()//2 + 30, 130, 30, (255, 0, 0))
        draw_soviet_button(btn_play, "ИГРАТЬ", hovers["play"], is_menu=True)
        draw_soviet_button(btn_about, "ПРО ИГРУ", hovers["about"], is_menu=True)
        draw_soviet_button(btn_scenarios, "СЦЕНАРИИ", hovers["scenarios"], is_menu=True)
        draw_soviet_button(btn_exit, "ВЫХОД", hovers["exit"], is_menu=True)

        if about_open:
            dim = pygame.Surface((WIDTH, HEIGHT)); dim.set_alpha(150); dim.fill((0,0,0)); screen.blit(dim, (0,0))
            pygame.draw.rect(screen, (30, 30, 30), about_rect, border_radius=10)
            pygame.draw.rect(screen, (200, 180, 50), about_rect, 3, border_radius=10)
            pygame.draw.rect(screen, (200, 50, 50), about_close_rect, border_radius=4)
            pygame.draw.line(screen, (255,255,255), (about_close_rect.left+7, about_close_rect.top+7), (about_close_rect.right-7, about_close_rect.bottom-7), 3)
            pygame.draw.line(screen, (255,255,255), (about_close_rect.right-7, about_close_rect.top+7), (about_close_rect.left+7, about_close_rect.bottom-7), 3)
            draw_gas_mask(screen, about_rect.x + 80, about_rect.centery, 50)
            lines = ["By: Eternal", "Версия 2.0", "Симулятор РБМК-1000", "Основано на реальных событиях"]
            y_off = about_rect.y + 50
            for line in lines:
                txt = font_large.render(line, True, (0, 255, 0))
                screen.blit(txt, (about_rect.x + 150, y_off))
                y_off += 40

    elif game_state == "SCENARIOS":
        dim = pygame.Surface((WIDTH, HEIGHT)); dim.set_alpha(150); dim.fill((0,0,0)); screen.blit(dim, (0,0))
        pygame.draw.rect(screen, (50, 40, 40), scenarios_rect, border_radius=10)
        pygame.draw.rect(screen, (220, 180, 50), scenarios_rect, 3, border_radius=10)
        title = font_title.render("СЦЕНАРИИ (МИССИИ)", True, (240, 200, 50))
        screen.blit(title, (scenarios_rect.centerx - title.get_width()//2, scenarios_rect.y + 15))
        draw_soviet_star(screen, scenarios_rect.x + 40, scenarios_rect.y + 40, 20, (255, 0, 0))
        pygame.draw.rect(screen, (200, 50, 50), scenarios_close_rect, border_radius=4)
        pygame.draw.line(screen, (255,255,255), (scenarios_close_rect.left+7, scenarios_close_rect.top+7), (scenarios_close_rect.right-7, scenarios_close_rect.bottom-7), 3)
        pygame.draw.line(screen, (255,255,255), (scenarios_close_rect.right-7, scenarios_close_rect.top+7), (scenarios_close_rect.left+7, scenarios_close_rect.bottom-7), 3)

        y_off = scenarios_rect.y + 80
        levels = [
            ("УРОВЕНЬ 1 (ЛЁГКИЙ)", [
                ("Разогнать реактор до 4000 МВт", scenario_btn_1_1),
                ("Спустить реактор до 2000 МВт", scenario_btn_1_2)
            ]),
            ("УРОВЕНЬ 2 (СРЕДНИЙ)", [
                ("Перейти на ДГ (выключить свет)", scenario_btn_2_1),
                ("Поднять БС до 1000 мм", scenario_btn_2_2)
            ]),
            ("УРОВЕНЬ 3 (СЛОЖНЫЙ)", [
                ("Взорвать реактор", scenario_btn_3_1),
                ("Запустить реактор (с 0)", scenario_btn_3_2)
            ])
        ]
        for lvl_name, tasks in levels:
            txt_level = font_bold.render(lvl_name, True, (200, 220, 200))
            screen.blit(txt_level, (scenarios_rect.x + 30, y_off))
            y_off += 30
            for task_text, btn_rect in tasks:
                hover = btn_rect.collidepoint(mx, my)
                col = (140 + int(hover * 40), 80 + int(hover * 30), 80 + int(hover * 30))
                pygame.draw.rect(screen, col, btn_rect, border_radius=5)
                pygame.draw.rect(screen, (230, 190, 60), btn_rect, 2, border_radius=5)
                txt = font.render(task_text, True, (255, 240 + int(hover*15), 180 + int(hover*75)))
                screen.blit(txt, (btn_rect.centerx - txt.get_width()//2, btn_rect.centery - txt.get_height()//2))
            y_off += 50

    else:
        # ---- ИГРОВОЙ ЭКРАН (ВЕСЬ ИНТЕРФЕЙС) ----
        screen.fill(COLOR_PANEL)
        pygame.draw.rect(screen, COLOR_PANEL_DARK, (15, 15, 680, 485), border_radius=4)
        pygame.draw.rect(screen, COLOR_FRAME, (15, 15, 680, 485), 2, border_radius=4)
        screen.blit(font_bold.render("МНЕМОСХЕМА АКТИВНОЙ ЗОНЫ РБМК-1000", True, COLOR_TEXT_DARK), (70, 30))

        cx_m, cy_m, letters_str = 345, 275, "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"
        for i in range(27):
            lx_val, ly_val = cx_m + (i - 13) * 15, cy_m + (i - 13) * 15
            if 0 <= i < len(letters_str):
                lt_surface = font_small.render(letters_str[i], True, (70, 80, 75))
                screen.blit(lt_surface, (lx_val - 3, 52)); screen.blit(lt_surface, (lx_val - 3, 442))
            num_surface = font_small.render(f"{i+1:02d}", True, (70, 80, 75))
            screen.blit(num_surface, (58, ly_val - 4)); screen.blit(num_surface, (452, ly_val - 4))

        for f_name, f_rect in filter_rects.items():
            pygame.draw.rect(screen, (150, 170, 150) if reactor.filter_mode == f_name else (115, 130, 118), f_rect, border_radius=3)
            pygame.draw.rect(screen, COLOR_FRAME, f_rect, 1, border_radius=3)
            f_txt = font_small.render(f_name, True, COLOR_TEXT_DARK)
            screen.blit(f_txt, (f_rect.centerx - f_txt.get_width()//2, f_rect.centery - f_txt.get_height()//2))

        if reactor.scala_state != "CALCULATING":
            pygame.draw.rect(screen, (170, 180, 170), rect_scala, border_radius=3)
            pygame.draw.rect(screen, COLOR_FRAME, rect_scala, 2, border_radius=3)
            if reactor.display_frozen:
                screen.blit(font_bold.render("ОШИБКА СВЯЗИ С СИСТЕМОЙ", True, (255, 50, 50)), (rect_scala.centerx - 85, rect_scala.centery - 6))
            else:
                screen.blit(font_bold.render("ЗАПРОС СИСТЕМЫ «СКАЛА»", True, COLOR_TEXT_DARK), (rect_scala.centerx - 85, rect_scala.centery - 6))
        else:
            pygame.draw.rect(screen, (240, 200, 30), rect_scala, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 200), rect_scala, 2, border_radius=3)
            screen.blit(font_bold.render("РАСЧЕТ...", True, (20, 20, 20)), (rect_scala.centerx - 30, rect_scala.centery - 6))

        pygame.draw.rect(screen, (100, 110, 105), (480, 120, 200, 135), border_radius=3)
        pygame.draw.rect(screen, COLOR_FRAME, (480, 120, 200, 135), 2, border_radius=3)
        selected_cell = reactor.core_dict.get(reactor.selected_grid_pos, None)
        if selected_cell:
            screen.blit(font_bold.render(f"КАНАЛ: {selected_cell['coord_name']}", True, (240, 240, 200)), (490, 128))
            screen.blit(font_small.render(f"Тип: {selected_cell['type'].upper()}", True, COLOR_TEXT_DARK), (490, 150))
            if reactor.display_frozen:
                screen.blit(font_small.render(f"Мощность: {selected_cell['power']}% (ЗАМОРОЖЕНО)", True, (150, 200, 150)), (490, 170))
            else:
                screen.blit(font_small.render(f"Мощность: {selected_cell['power']}%", True, COLOR_TEXT_DARK), (490, 170))
            screen.blit(font_small.render(f"Стержень: {reactor.rods_pos:.1f} м", True, COLOR_TEXT_DARK), (490, 190))
            screen.blit(font_small.render(f"Т. воды: {reactor.fuel_temp:.1f} °C", True, COLOR_TEXT_DARK), (490, 210))

        for ar_rect, ar_lbl in [(btn_arrow_u, "▲"), (btn_arrow_d, "▼"), (btn_arrow_l, "◄"), (btn_arrow_r, "►")]:
            pygame.draw.rect(screen, (120, 130, 125), ar_rect, border_radius=2)
            pygame.draw.rect(screen, COLOR_FRAME, ar_rect, 1, border_radius=2)
            ar_t = font_small.render(ar_lbl, True, COLOR_TEXT_DARK)
            screen.blit(ar_t, (ar_rect.centerx - ar_t.get_width()//2, ar_rect.centery - ar_t.get_height()//2))

        pygame.draw.rect(screen, (95, 105, 98), (480, 25, 200, 90), border_radius=3)
        pygame.draw.rect(screen, COLOR_FRAME, (480, 25, 200, 90), 2, border_radius=3)
        pygame.draw.circle(screen, (30, 35, 30), (620, 45), 12); pygame.draw.circle(screen, (15, 20, 15), (620, 45), 12, 2)
        screen.blit(font_small.render("ПЕРЕЖОГ", True, COLOR_TEXT_DARK), (598, 60))
        screen.blit(font_bold.render("ПЯТАЧОК КОНТРОЛЯ", True, COLOR_TEXT_DARK), (490, 32))
        blink_on = (current_time // 300) % 2 == 0

        # ---- БЛИНКЕРЫ (с исправленным порядком) ----
        if reactor.display_frozen:
            blinkers_data = [
                ("ОТКАЗ ИВС «СКАЛА»", True, (220, 180, 30)),
                ("АЗ: ПРЕВЫШ. МОЩ.", False, (60, 68, 62)),
                ("АЗ: СКОРОСТЬ Т<20с", False, (60, 68, 62)),
                ("АЗ: РАСХОД ВОДЫ", False, (60, 68, 62)),
                ("АЗ: ДАВЛЕНИЕ БС", False, (60, 68, 62)),
                ("АЗ: УРОВЕНЬ БС", False, (60, 68, 62)),
                ("ОЗР < 15 СТЕРЖ.", False, (60, 68, 62)),
                ("ПОЛОМКА ТГ-7", False, (60, 68, 62)),
                ("ПОЛОМКА ТГ-8", False, (60, 68, 62)),
                ("ОТКАЗ ГЦН", False, (60, 68, 62)),
                ("ОТКАЗ ГЦН", False, (60, 68, 62)),
                ("ПЕРЕГРЕВ КОНДЕНСАТОРА", False, (60, 68, 62)),
                ("ДГ РАБОТАЕТ", False, (60, 68, 62)),
                ("ПЕРЕГРЕВ ГРАФИТА", False, (60, 68, 62)),
                ("ПАР КМПЦ ВЫШЕ", False, (60, 68, 62)),
                ("НЕИСПРАВНОСТЬ СУЗ", False, (60, 68, 62)),
                ("ПОДПИТКА БС: МАКС", False, (60, 68, 62))
            ]
        else:
            bru_alarm = reactor.bru_overheat_timer > 4.0 and reactor.bru_enabled
            dg_alarm = reactor.dg_running
            blinkers_data = [
                ("ОТКАЗ ИВС «СКАЛА»", reactor.scala_state == "CALCULATING", (220, 180, 30)),
                ("АЗ: ПРЕВЫШ. МОЩ.", reactor.power > 3300.0, (220, 30, 30)),
                ("АЗ: СКОРОСТЬ Т<20с", reactor.power_vel > 200.0, (220, 30, 30)),
                ("АЗ: РАСХОД ВОДЫ", reactor.gcn_count < 4, (220, 30, 30)),
                ("АЗ: ДАВЛЕНИЕ БС", reactor.bs_pressure > 8.5, (220, 30, 30)),
                ("АЗ: УРОВЕНЬ БС", abs(reactor.bs_level) > 800.0, (220, 30, 30)),
                ("ОЗР < 15 СТЕРЖ.", reactor.ozr < 15.0, (220, 30, 30)),
                ("ПОЛОМКА ТГ-7", reactor.oil_temp >= PEN_OIL_CRITICAL, (220, 30, 30)),
                ("ПОЛОМКА ТГ-8", reactor.oil_temp >= PEN_OIL_CRITICAL, (220, 30, 30)),
                ("ОТКАЗ ГЦН", reactor.gcn_count == 0 or reactor.oil_temp >= PEN_OIL_CRITICAL, (220, 30, 30)),
                ("ОТКАЗ ГЦН", 4 <= reactor.gcn_count < 8, (220, 180, 30)),
                ("ПЕРЕГРЕВ КОНДЕНСАТОРА", bru_alarm, (220, 30, 30)),
                ("ДГ РАБОТАЕТ", dg_alarm, (220, 30, 30)),
                ("ПЕРЕГРЕВ ГРАФИТА", reactor.fuel_temp > 700.0, (220, 180, 30)),
                ("ПАР КМПЦ ВЫШЕ", reactor.steam_fraction > 20.0, (220, 180, 30)),
                ("НЕИСПРАВНОСТЬ СУЗ", reactor.az5_active and reactor.rods_pos > 80.0, (220, 180, 30)),
                ("ПОДПИТКА БС: МАКС", reactor.feed_water_flow < 2500.0, (220, 180, 30))
            ]

        for idx, (b_text, b_act, b_col) in enumerate(blinkers_data):
            box_rect = pygame.Rect(480 + (idx % 4) * 50, 280 + (idx // 4) * 56, 48, 52)
            pygame.draw.rect(screen, b_col if (b_act and blink_on) else (60, 68, 62), box_rect, border_radius=3)
            pygame.draw.rect(screen, COLOR_FRAME, box_rect, 1, border_radius=3)
            small_font = pygame.font.Font(None, 9)
            words = b_text.split()
            if len(words) > 2:
                line1 = words[0] + " " + words[1]
                line2 = " ".join(words[2:])
            else:
                line1 = b_text
                line2 = ""
            wt1 = small_font.render(line1, True, (20, 20, 20) if (b_act and blink_on) else (150, 160, 155))
            screen.blit(wt1, (box_rect.centerx - wt1.get_width()//2, box_rect.y + 4))
            if line2:
                wt2 = small_font.render(line2, True, (20, 20, 20) if (b_act and blink_on) else (150, 160, 155))
                screen.blit(wt2, (box_rect.centerx - wt2.get_width()//2, box_rect.y + 18))

        # ---- ЯЧЕЙКИ АКТИВНОЙ ЗОНЫ ----
        for ch in reactor.core_map:
            base = list(ch["color"])
            skip_draw = False
            if reactor.filter_mode == "RODS" and ch["type"] not in ["az", "ar", "lar"]: skip_draw = True
            elif reactor.filter_mode == "POWER" and ch["type"] != "fuel": skip_draw = True
            elif reactor.filter_mode == "AZ" and ch["type"] != "az": skip_draw = True
            if skip_draw: continue
            if ch["type"] == "fuel":
                if reactor.display_frozen:
                    pass
                else:
                    temp_glow = max(0.0, min(1.0, (reactor.fuel_temp - 300) / 1000.0))
                    base[0] = min(255, int(base[0] + temp_glow * 80)); base[1] = max(0, int(base[1] - temp_glow * 60)); base[2] = max(0, int(base[2] - temp_glow * 60))
                    if reactor.power > 1000.0: flicker = random.uniform(-10, 10) * (reactor.power / 4000.0); base = [max(0, min(255, c + flicker)) for c in base]
            elif ch["type"] in ["az", "ar", "lar", "usp", "pk"]: base = [int(c * (0.35 + (1.0 - (reactor.rods_pos / 100.0)) * 0.65)) for c in base]
            pygame.draw.rect(screen, base, (ch["x"], ch["y"], 11, 11), border_radius=1)
            if (ch["grid_x"], ch["grid_y"]) == reactor.selected_grid_pos: pygame.draw.rect(screen, (255, 255, 0), (ch["x"] - 1, ch["y"] - 1, 13, 13), 2)

        for idx, (px, py) in enumerate([(510, 75), (555, 75), (510, 100), (555, 100)]):
            pygame.draw.circle(screen, (40, 255, 40) if reactor.pyatachok[idx] else (20, 60, 20), (px, py), 6)
            screen.blit(font_small.render(["С-1", "С-2", "С-3", "С-4"][idx], True, (200, 220, 200)), (px - 8, py - 18))

        if not reactor.display_frozen and (reactor.power > 3300.0 or reactor.fuel_temp > 900.0 or reactor.gcn_bearing_temp >= 120.0) and (current_time // 250) % 2 == 0:
            pygame.draw.circle(screen, (255, 30, 30), (620, 45), 10)

        # ---- ПАНЕЛЬ СУЗ ----
        pygame.draw.rect(screen, COLOR_PANEL_DARK, (15, 510, 680, 195), border_radius=4)
        pygame.draw.rect(screen, COLOR_FRAME, (15, 510, 680, 195), 2, border_radius=4)
        screen.blit(font_bold.render("УПРАВЛЕНИЕ И ПРОФИЛЬ ПОГРУЖЕНИЯ СТЕРЖНЕЙ СУЗ", True, COLOR_TEXT_DARK), (25, 520))
        if reactor.ar_active: screen.blit(font_bold.render("(БЛОКИРОВАНО АВТОМАТИКОЙ (АР ВКЛЮЧЕН))", True, (180, 40, 40)), (360, 520))
        elif reactor.az5_locked_out: screen.blit(font_bold.render("(БЛОКИРОВКА АЗ-5: ТРЕБУЕТСЯ СБРОС)", True, (220, 180, 30)), (340, 520))

        pygame.draw.rect(screen, (60, 65, 60), (30, 565, 650, 80))
        for i in range(16):
            rx_rod = 30 + int(i * (650 / 16)) + 20
            pygame.draw.line(screen, (30, 35, 30), (rx_rod, 565), (rx_rod, 645), 6)
            if reactor.display_frozen:
                pass
            else:
                pygame.draw.line(screen, (220, 220, 220), (rx_rod, 565), (rx_rod, 565 + (reactor.rods_pos / 100.0) * 80), 4)

        pygame.draw.rect(screen, (150, 165, 150), rect_suz_up, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_suz_up, 2, border_radius=3)
        screen.blit(font_small.render("КЛЮЧ СУЗ: ВЫЕМКА", True, COLOR_TEXT_DARK), (rect_suz_up.centerx - 50, rect_suz_up.centery - 4))
        pygame.draw.rect(screen, (150, 165, 150), rect_suz_down, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_suz_down, 2, border_radius=3)
        screen.blit(font_small.render("КЛЮЧ СУЗ: ПОГРУЖЕНИЕ", True, COLOR_TEXT_DARK), (rect_suz_down.centerx - 60, rect_suz_down.centery - 4))

        # ---- ПРАВАЯ ПАНЕЛЬ – ДАТЧИКИ ----
        pygame.draw.rect(screen, COLOR_PANEL_DARK, (715, 15, 550, 690), border_radius=4); pygame.draw.rect(screen, COLOR_FRAME, (715, 15, 550, 690), 2, border_radius=4)

        # Определяем значения для отображения
        if reactor.display_frozen:
            power_val = reactor.frozen_power if hasattr(reactor, 'frozen_power') else reactor.power
            elec_val = reactor.frozen_elec_power if hasattr(reactor, 'frozen_elec_power') else reactor.elec_power
            fuel_val = reactor.frozen_fuel_temp if hasattr(reactor, 'frozen_fuel_temp') else reactor.fuel_temp
            steam_val = reactor.frozen_steam_fraction if hasattr(reactor, 'frozen_steam_fraction') else reactor.steam_fraction
            xenon_val = reactor.frozen_xenon if hasattr(reactor, 'frozen_xenon') else reactor.xenon
            ozr_val = reactor.frozen_ozr if hasattr(reactor, 'frozen_ozr') else reactor.ozr
            bs_val = reactor.frozen_bs_level if hasattr(reactor, 'frozen_bs_level') else reactor.bs_level
            bearing_val = reactor.frozen_gcn_bearing_temp if hasattr(reactor, 'frozen_gcn_bearing_temp') else reactor.gcn_bearing_temp
            oil_val = reactor.frozen_oil_temp if hasattr(reactor, 'frozen_oil_temp') else reactor.oil_temp
        else:
            power_val = reactor.power
            elec_val = reactor.elec_power
            fuel_val = reactor.fuel_temp
            steam_val = reactor.steam_fraction
            xenon_val = reactor.xenon
            ozr_val = reactor.display_ozr
            bs_val = reactor.bs_level
            bearing_val = reactor.gcn_bearing_temp
            oil_val = reactor.oil_temp

        # Датчики (9 основных + дизель)
        gauges = [
            ("МОЩНОСТЬ (МВт)", power_val, 0, 4000, 15),
            ("ЭЛЕКТРОЭНЕРГИЯ (МВт)", elec_val, 0, 1200, 47),
            ("ТЕМП. ТОПЛИВА (°C)", fuel_val, 0, 2000, 79),
            ("ТЕМП. ВО ВОДЫ (°C)", reactor.inlet_temp, 200, 350, 111),
            ("ПАРОСОДЕРЖАНИЕ (%)", steam_val, 0, 100, 143),
            ("КСЕНОН-135 (%)", xenon_val, 0, 100, 175),
            ("ОЗР (СКАЛА-В)", ozr_val, 0, 50, 207),
            ("ПОДШИПНИКИ ГЦН (°C)", bearing_val, 0, 600, 239),
            ("ДИЗЕЛЬ (мин)", reactor.dg_fuel, 0, 10, 271),
            ("ТЕМП. МАСЛА (°C)", oil_val, 0, 100, 303)
        ]
        for lbl, val, min_v, max_v, gy in gauges:
            pygame.draw.rect(screen, COLOR_PANEL_DARK, (730, gy, 405, 30), border_radius=2); pygame.draw.rect(screen, COLOR_FRAME, (730, gy, 405, 30), 2, border_radius=2)
            screen.blit(font_bold.render(lbl, True, COLOR_TEXT_DARK), (738, gy + 8))
            pygame.draw.rect(screen, (235, 240, 230), (890, gy + 3, 150, 24))
            for t in range(0, 150, 13): pygame.draw.line(screen, (180, 185, 175), (890 + t, gy + 3), (890 + t, gy + 10), 1)
            pygame.draw.rect(screen, (15, 25, 15), (1050, gy + 3, 78, 24), border_radius=2)
            norm = max(0.0, min(1.0, (val - min_v) / (max_v - min_v)))
            px = 890 + norm * 150
            pygame.draw.line(screen, (255, 30, 30), (px, gy + 3), (px, gy + 27), 3)
            if reactor.display_frozen:
                v_col = (40, 255, 40)
            else:
                v_col = (40, 255, 40)
                if (lbl.startswith("МОЩ") and val > 3300) or (lbl.startswith("ТЕМП") and val > 900) or (lbl.startswith("ПОДШИП") and val >= 450) or (lbl.startswith("ОЗР") and val < 15.0 and (current_time//200)%2==0) or (lbl.startswith("ТЕМП. МАСЛА") and val >= 80.0) or (lbl.startswith("ДИЗЕЛЬ") and val <= 0.0):
                    v_col = (255, 40, 40)
                elif lbl.startswith("ОЗР") and val < 15.0:
                    v_col = (255, 255, 40)
            txt_v = font_bold.render(f"{val:.1f}", True, v_col); screen.blit(txt_v, (1089 - txt_v.get_width()//2, gy + 9))

        # ---- БЛОК УПРАВЛЕНИЯ БС (датчик + кнопки + и -) ----
        bs_cx, bs_cy = 1180, 155
        bs_radius = 50
        draw_bs_gauge(bs_cx, bs_cy, bs_radius, reactor.bs_level, BS_MIN, BS_MAX)
        lbl_bs = font_bold.render("УРОВЕНЬ БС", True, (200, 220, 200))
        screen.blit(lbl_bs, (bs_cx - lbl_bs.get_width()//2, bs_cy - bs_radius - 20))

        pygame.draw.rect(screen, (140, 150, 145), rect_bs_plus, border_radius=3)
        pygame.draw.rect(screen, COLOR_FRAME, rect_bs_plus, 1, border_radius=3)
        txt_plus = font_bold.render("+", True, COLOR_TEXT_DARK)
        screen.blit(txt_plus, (rect_bs_plus.centerx - txt_plus.get_width()//2, rect_bs_plus.centery - txt_plus.get_height()//2))
        pygame.draw.rect(screen, (140, 150, 145), rect_bs_minus, border_radius=3)
        pygame.draw.rect(screen, COLOR_FRAME, rect_bs_minus, 1, border_radius=3)
        txt_minus = font_bold.render("-", True, COLOR_TEXT_DARK)
        screen.blit(txt_minus, (rect_bs_minus.centerx - txt_minus.get_width()//2, rect_bs_minus.centery - txt_minus.get_height()//2))

        # ---- ПЕРЕКЛЮЧАТЕЛИ ----
        draw_soviet_switch(780, 380, "ЗАЩ. ТГ-7", reactor.tg7_prot, reactor.anim_angles["tg7"])
        draw_soviet_switch(890, 380, "АВТОМ. БС", reactor.bs_auto, reactor.anim_angles["bs_auto"])
        draw_soviet_switch(1000, 380, "ЗАЩ. ВОДЫ", reactor.prot_water, reactor.anim_angles["p_water"])
        draw_soviet_switch(780, 455, "ЗАЩ. ТГ-8", reactor.tg8_prot, reactor.anim_angles["tg8"])
        draw_soviet_switch(890, 455, "РЕГУЛЯТОР АР", reactor.ar_active, reactor.anim_angles["ar"])
        draw_soviet_switch(1000, 455, "ЗАЩ. ОЗР", reactor.prot_ozr, reactor.anim_angles["p_ozr"])
        draw_soviet_switch(1090, 380, f"ГЦН: {reactor.gcn_count}/8", True, reactor.anim_angles["gcn"])
        draw_soviet_switch(1000, 455, f"ПЭН: {'ВКЛ' if reactor.pen_enabled else 'ВЫКЛ'}", reactor.pen_enabled, reactor.anim_angles["pen"])
        draw_soviet_switch(1090, 455, f"БРУ-К: {'ВКЛ' if reactor.bru_enabled else 'ВЫКЛ'}", reactor.bru_enabled, reactor.anim_angles["bru"])
        draw_soviet_switch(1170, 455, f"ДГ: {'ВКЛ' if reactor.dg_enabled else 'ВЫКЛ'}", reactor.dg_enabled, reactor.anim_angles["dg"])

        for rect_b, lbl_b in [(rect_gcn_minus, "-"), (rect_gcn_plus, "+")]:
            pygame.draw.rect(screen, (140, 150, 145), rect_b, border_radius=2); pygame.draw.rect(screen, COLOR_FRAME, rect_b, 1, border_radius=2)
            bt_txt = font_bold.render(lbl_b, True, COLOR_TEXT_DARK); screen.blit(bt_txt, (rect_b.centerx - bt_txt.get_width()//2, rect_b.centery - bt_txt.get_height()//2))

        pygame.draw.rect(screen, COLOR_PANEL_DARK, (730, 495, 400, 75), border_radius=4); pygame.draw.rect(screen, COLOR_FRAME, (730, 495, 400, 75), 2, border_radius=4)
        screen.blit(font_bold.render("УКАЗАТЕЛИ ПОЛОЖЕНИЯ СТЕРЖНЕЙ ЛАР", True, COLOR_TEXT_DARK), (740, 503))
        for i in range(8):
            lx = 750 + i * 45
            pygame.draw.rect(screen, (50, 55, 50), (lx, 523, 20, 38))
            if reactor.display_frozen:
                pos = reactor.lar_positions[i] if hasattr(reactor, 'lar_positions') else 50.0
            else:
                pos = reactor.lar_positions[i]
            pygame.draw.rect(screen, (40, 130, 255), (lx, 523, 20, int((pos / 100.0) * 38)))
            pygame.draw.line(screen, (255, 40, 40), (lx - 3, 542), (lx + 23, 542), 2)

        pygame.draw.rect(screen, (20, 25, 20), (730, 575, 400, 72), border_radius=4); pygame.draw.rect(screen, COLOR_FRAME, (730, 575, 400, 72), 2, border_radius=4)
        log_y = 581
        visible_logs = [msg for msg in reactor.event_log if not msg.startswith("СКРЫТО:")]
        for log_msg in visible_logs[-3:]:
            screen.blit(font_small.render(log_msg, True, (40, 230, 40)), (736, log_y))
            log_y += 18

        # ---- КНОПКИ (СБРОС АЗ-5, ВЫБЕГ ТГ, СИРЕНА, БЛОК АЗ-5, АЗ-5) ----
        pygame.draw.rect(screen, (160, 150, 140), rect_az5_reset, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_az5_reset, 2, border_radius=3)
        reset_txt = font_small.render("СБРОС СИГНАЛА АЗ-5", True, COLOR_TEXT_DARK); screen.blit(reset_txt, (rect_az5_reset.centerx - reset_txt.get_width()//2, rect_az5_reset.centery - reset_txt.get_height()//2))
        pygame.draw.rect(screen, (140, 160, 150), rect_turbine_coast, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_turbine_coast, 2, border_radius=3)
        coast_txt = font_small.render(f"ВЫБЕГ ТГ: {'ВКЛ' if reactor.turbine_coasting else 'ВЫКЛ'}", True, COLOR_TEXT_DARK); screen.blit(coast_txt, (rect_turbine_coast.centerx - coast_txt.get_width()//2, rect_turbine_coast.centery - coast_txt.get_height()//2))

        siren_state = "ВКЛ" if reactor.siren_enabled else "ВЫКЛ"
        col_siren = (160, 150, 140) if reactor.siren_enabled else (100, 100, 100)
        pygame.draw.rect(screen, col_siren, rect_siren_off, border_radius=3)
        pygame.draw.rect(screen, COLOR_FRAME, rect_siren_off, 2, border_radius=3)
        siren_txt = font_small.render(f"СИРЕНА: {siren_state}", True, COLOR_TEXT_DARK)
        screen.blit(siren_txt, (rect_siren_off.centerx - siren_txt.get_width()//2, rect_siren_off.centery - siren_txt.get_height()//2))

        pygame.draw.rect(screen, COLOR_PANEL_DARK, rect_override, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_override, 2, border_radius=3)
        if not reactor.override_cap_open:
            pygame.draw.rect(screen, (150, 40, 40), (rect_override.x+4, rect_override.y+4, rect_override.width-8, rect_override.height-8), border_radius=3)
            pygame.draw.rect(screen, (200, 50, 50), (rect_override.x+4, rect_override.y+4, rect_override.width-8, rect_override.height-8), 2, border_radius=3)
            lbl_block1 = font_bold.render("БЛОК.", True, (240, 240, 240)); lbl_block2 = font_bold.render("АЗ-5", True, (240, 240, 240))
            screen.blit(lbl_block1, (rect_override.centerx - lbl_block1.get_width()//2, rect_override.centery - 8))
            screen.blit(lbl_block2, (rect_override.centerx - lbl_block2.get_width()//2, rect_override.centery + 4))
        else:
            pygame.draw.circle(screen, (30, 30, 30), rect_override.center, 22)
            if reactor.override_key_inserted:
                if not reactor.override_key_turned: pygame.draw.rect(screen, (220, 220, 40), (rect_override.centerx-4, rect_override.centery-18, 8, 36))
                else: pygame.draw.rect(screen, (40, 220, 40), (rect_override.centerx-18, rect_override.centery-4, 36, 8))

        az5_cx, az5_cy = rect_az5_button.centerx, rect_az5_button.centery
        pygame.draw.rect(screen, COLOR_PANEL_DARK, rect_az5_button, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_az5_button, 2, border_radius=3)
        az5_cap_col = (180, 40, 40) if not reactor.az5_cap_open else (90, 100, 95)
        az5_inner = pygame.Rect(rect_az5_button.x + 6, rect_az5_button.y + 6, rect_az5_button.width - 12, rect_az5_button.height - 12)
        pygame.draw.rect(screen, az5_cap_col, az5_inner, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, az5_inner, 2, border_radius=3)
        az5_lbl = "АЗ-5 (КРЫШКА)" if not reactor.az5_cap_open else ("АЗ-5 ВКЛ" if reactor.az5_active else "АЗ-5 ВЫКЛ")
        az5_t = font_small.render(az5_lbl, True, (240, 240, 240) if not reactor.az5_cap_open else (255, 255, 0))
        screen.blit(az5_t, (az5_cx - az5_t.get_width()//2, az5_cy - az5_t.get_height()//2))

        if not reactor.station_power: blackout = pygame.Surface((WIDTH, HEIGHT)); blackout.set_alpha(225); blackout.fill((3, 5, 3)); screen.blit(blackout, (0, 0))
# ========== КОНЕЦ ЧАСТИ 12a ==========
# ========== ЧАСТЬ 12b: ОТРИСОВКА БС И ОСТАЛЬНЫЕ ЭЛЕМЕНТЫ ==========
        # ---- БЛОК УПРАВЛЕНИЯ БС ----
        bs_cx, bs_cy = 1180, 155
        bs_radius = 50
        draw_bs_gauge(bs_cx, bs_cy, bs_radius, reactor.bs_level, BS_MIN, BS_MAX)
        lbl_bs = font_bold.render("УРОВЕНЬ БС", True, (200, 220, 200))
        screen.blit(lbl_bs, (bs_cx - lbl_bs.get_width()//2, bs_cy - bs_radius - 20))

        pygame.draw.rect(screen, (140, 150, 145), rect_bs_plus, border_radius=3)
        pygame.draw.rect(screen, COLOR_FRAME, rect_bs_plus, 1, border_radius=3)
        txt_plus = font_bold.render("+", True, COLOR_TEXT_DARK)
        screen.blit(txt_plus, (rect_bs_plus.centerx - txt_plus.get_width()//2, rect_bs_plus.centery - txt_plus.get_height()//2))
        pygame.draw.rect(screen, (140, 150, 145), rect_bs_minus, border_radius=3)
        pygame.draw.rect(screen, COLOR_FRAME, rect_bs_minus, 1, border_radius=3)
        txt_minus = font_bold.render("-", True, COLOR_TEXT_DARK)
        screen.blit(txt_minus, (rect_bs_minus.centerx - txt_minus.get_width()//2, rect_bs_minus.centery - txt_minus.get_height()//2))

        # ---- ПЕРЕКЛЮЧАТЕЛИ (с новыми кнопками) ----
        draw_soviet_switch(780, 380, "ЗАЩ. ТГ-7", reactor.tg7_prot, reactor.anim_angles["tg7"])
        draw_soviet_switch(890, 380, "АВТОМ. БС", reactor.bs_auto, reactor.anim_angles["bs_auto"])
        draw_soviet_switch(1000, 380, "ЗАЩ. ВОДЫ", reactor.prot_water, reactor.anim_angles["p_water"])
        draw_soviet_switch(780, 455, "ЗАЩ. ТГ-8", reactor.tg8_prot, reactor.anim_angles["tg8"])
        draw_soviet_switch(890, 455, "РЕГУЛЯТОР АР", reactor.ar_active, reactor.anim_angles["ar"])
        draw_soviet_switch(1000, 455, "ЗАЩ. ОЗР", reactor.prot_ozr, reactor.anim_angles["p_ozr"])
        draw_soviet_switch(1090, 380, f"ГЦН: {reactor.gcn_count}/8", True, reactor.anim_angles["gcn"])
        draw_soviet_switch(1000, 455, f"ПЭН: {'ВКЛ' if reactor.pen_enabled else 'ВЫКЛ'}", reactor.pen_enabled, reactor.anim_angles["pen"])
        draw_soviet_switch(1090, 455, f"БРУ-К: {'ВКЛ' if reactor.bru_enabled else 'ВЫКЛ'}", reactor.bru_enabled, reactor.anim_angles["bru"])
        draw_soviet_switch(1170, 455, f"ДГ: {'ВКЛ' if reactor.dg_enabled else 'ВЫКЛ'}", reactor.dg_enabled, reactor.anim_angles["dg"])

        for rect_b, lbl_b in [(rect_gcn_minus, "-"), (rect_gcn_plus, "+")]:
            pygame.draw.rect(screen, (140, 150, 145), rect_b, border_radius=2); pygame.draw.rect(screen, COLOR_FRAME, rect_b, 1, border_radius=2)
            bt_txt = font_bold.render(lbl_b, True, COLOR_TEXT_DARK); screen.blit(bt_txt, (rect_b.centerx - bt_txt.get_width()//2, rect_b.centery - bt_txt.get_height()//2))

        pygame.draw.rect(screen, COLOR_PANEL_DARK, (730, 495, 400, 75), border_radius=4); pygame.draw.rect(screen, COLOR_FRAME, (730, 495, 400, 75), 2, border_radius=4)
        screen.blit(font_bold.render("УКАЗАТЕЛИ ПОЛОЖЕНИЯ СТЕРЖНЕЙ ЛАР", True, COLOR_TEXT_DARK), (740, 503))
        for i in range(8):
            lx = 750 + i * 45
            pygame.draw.rect(screen, (50, 55, 50), (lx, 523, 20, 38))
            if reactor.display_frozen:
                pos = reactor.lar_positions[i] if hasattr(reactor, 'lar_positions') else 50.0
            else:
                pos = reactor.lar_positions[i]
            pygame.draw.rect(screen, (40, 130, 255), (lx, 523, 20, int((pos / 100.0) * 38)))
            pygame.draw.line(screen, (255, 40, 40), (lx - 3, 542), (lx + 23, 542), 2)

        pygame.draw.rect(screen, (20, 25, 20), (730, 575, 400, 72), border_radius=4); pygame.draw.rect(screen, COLOR_FRAME, (730, 575, 400, 72), 2, border_radius=4)
        log_y = 581
        visible_logs = [msg for msg in reactor.event_log if not msg.startswith("СКРЫТО:")]
        for log_msg in visible_logs[-3:]:
            screen.blit(font_small.render(log_msg, True, (40, 230, 40)), (736, log_y))
            log_y += 18

        # Кнопки
        pygame.draw.rect(screen, (160, 150, 140), rect_az5_reset, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_az5_reset, 2, border_radius=3)
        reset_txt = font_small.render("СБРОС СИГНАЛА АЗ-5", True, COLOR_TEXT_DARK); screen.blit(reset_txt, (rect_az5_reset.centerx - reset_txt.get_width()//2, rect_az5_reset.centery - reset_txt.get_height()//2))
        pygame.draw.rect(screen, (140, 160, 150), rect_turbine_coast, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_turbine_coast, 2, border_radius=3)
        coast_txt = font_small.render(f"ВЫБЕГ ТГ: {'ВКЛ' if reactor.turbine_coasting else 'ВЫКЛ'}", True, COLOR_TEXT_DARK); screen.blit(coast_txt, (rect_turbine_coast.centerx - coast_txt.get_width()//2, rect_turbine_coast.centery - coast_txt.get_height()//2))

        siren_state = "ВКЛ" if reactor.siren_enabled else "ВЫКЛ"
        col_siren = (160, 150, 140) if reactor.siren_enabled else (100, 100, 100)
        pygame.draw.rect(screen, col_siren, rect_siren_off, border_radius=3)
        pygame.draw.rect(screen, COLOR_FRAME, rect_siren_off, 2, border_radius=3)
        siren_txt = font_small.render(f"СИРЕНА: {siren_state}", True, COLOR_TEXT_DARK)
        screen.blit(siren_txt, (rect_siren_off.centerx - siren_txt.get_width()//2, rect_siren_off.centery - siren_txt.get_height()//2))

        pygame.draw.rect(screen, COLOR_PANEL_DARK, rect_override, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_override, 2, border_radius=3)
        if not reactor.override_cap_open:
            pygame.draw.rect(screen, (150, 40, 40), (rect_override.x+4, rect_override.y+4, rect_override.width-8, rect_override.height-8), border_radius=3)
            pygame.draw.rect(screen, (200, 50, 50), (rect_override.x+4, rect_override.y+4, rect_override.width-8, rect_override.height-8), 2, border_radius=3)
            lbl_block1 = font_bold.render("БЛОК.", True, (240, 240, 240)); lbl_block2 = font_bold.render("АЗ-5", True, (240, 240, 240))
            screen.blit(lbl_block1, (rect_override.centerx - lbl_block1.get_width()//2, rect_override.centery - 8))
            screen.blit(lbl_block2, (rect_override.centerx - lbl_block2.get_width()//2, rect_override.centery + 4))
        else:
            pygame.draw.circle(screen, (30, 30, 30), rect_override.center, 22)
            if reactor.override_key_inserted:
                if not reactor.override_key_turned: pygame.draw.rect(screen, (220, 220, 40), (rect_override.centerx-4, rect_override.centery-18, 8, 36))
                else: pygame.draw.rect(screen, (40, 220, 40), (rect_override.centerx-18, rect_override.centery-4, 36, 8))

        az5_cx, az5_cy = rect_az5_button.centerx, rect_az5_button.centery
        pygame.draw.rect(screen, COLOR_PANEL_DARK, rect_az5_button, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, rect_az5_button, 2, border_radius=3)
        az5_cap_col = (180, 40, 40) if not reactor.az5_cap_open else (90, 100, 95)
        az5_inner = pygame.Rect(rect_az5_button.x + 6, rect_az5_button.y + 6, rect_az5_button.width - 12, rect_az5_button.height - 12)
        pygame.draw.rect(screen, az5_cap_col, az5_inner, border_radius=3); pygame.draw.rect(screen, COLOR_FRAME, az5_inner, 2, border_radius=3)
        az5_lbl = "АЗ-5 (КРЫШКА)" if not reactor.az5_cap_open else ("АЗ-5 ВКЛ" if reactor.az5_active else "АЗ-5 ВЫКЛ")
        az5_t = font_small.render(az5_lbl, True, (240, 240, 240) if not reactor.az5_cap_open else (255, 255, 0))
        screen.blit(az5_t, (az5_cx - az5_t.get_width()//2, az5_cy - az5_t.get_height()//2))

        if not reactor.station_power: blackout = pygame.Surface((WIDTH, HEIGHT)); blackout.set_alpha(225); blackout.fill((3, 5, 3)); screen.blit(blackout, (0, 0))
# ========== КОНЕЦ ЧАСТИ 12b ==========
# ========== ЧАСТЬ 13: САС, МЕНЮ ЧИТОВ, МАГНИТОФОН ==========
        sas_alerts = []
        if not reactor.display_frozen:
            if reactor.fuel_temp > 900: sas_alerts.append("ПЕРЕГРЕВ ТОПЛИВА")
            if reactor.steam_fraction > 20: sas_alerts.append("КРИТИЧЕСКОЕ ПАРОСОДЕРЖАНИЕ")
            if reactor.ozr < 15: sas_alerts.append("НИЗКИЙ ОЗР (<15 СТЕРЖНЕЙ)")
            if abs(reactor.bs_level) > 800: sas_alerts.append("КРИТИЧЕСКИЙ УРОВЕНЬ БС")
            if not reactor.station_power: sas_alerts.append("ПОЛНЫЙ БЛЭКАУТ СТАНЦИИ")
            if reactor.gcn_bearing_temp >= 450.0: sas_alerts.append("КРИТИЧЕСКИЙ НАГРЕВ ПОДШИПНИКОВ ГЦН")
            if reactor.oil_temp >= 80.0: sas_alerts.append("КРИТИЧЕСКАЯ ТЕМП. МАСЛА ПЭН")
            if reactor.bru_overheat_timer > 4.0 and reactor.bru_enabled:
                sas_alerts.append("ПЕРЕГРЕВ КОНДЕНСАТОРА БРУ-К")
        else:
            sas_alerts.append("СИСТЕМА НЕ ОТВЕЧАЕТ")
        if sas_alerts and (current_time // 400) % 2 == 0:
            sas_surf = font_bold.render("  //  СПЕЦСИГНАЛ САС: " + "  ***  ".join(sas_alerts) + "  //  ", True, (255, 50, 50))
            screen.blit(sas_surf, (WIDTH//2 - sas_surf.get_width()//2, 2))

        pygame.draw.rect(screen, (110, 120, 115), rect_menu_btn, border_radius=5); pygame.draw.rect(screen, COLOR_FRAME, rect_menu_btn, 2, border_radius=5)
        for i in range(3): pygame.draw.line(screen, COLOR_TEXT_DARK, (rect_menu_btn.left + 6, rect_menu_btn.top + 8 + i*9), (rect_menu_btn.right - 6, rect_menu_btn.top + 8 + i*9), 3)

        t_surf = font_bold.render(f"СМЕНА: {int(reactor.shift_timer//3600)+11:02d}:{int((reactor.shift_timer%3600)//60):02d}:{int(reactor.shift_timer%60):02d}", True, (200, 220, 200))
        screen.blit(t_surf, (25, 432))

        if menu_open:
            dim = pygame.Surface((WIDTH, HEIGHT)); dim.set_alpha(150); dim.fill((0, 0, 0)); screen.blit(dim, (0, 0))
            pygame.draw.rect(screen, (80, 30, 30), menu_rect, border_radius=8); pygame.draw.rect(screen, (220, 180, 50), menu_rect, 4, border_radius=8) 
            draw_soviet_star(screen, menu_rect.centerx, menu_rect.centery, 160, (110, 35, 35))
            txt_title = font_large.render("ЧИТЫ И СЦЕНАРИИ АВАРИЙ", True, (240, 200, 50)); screen.blit(txt_title, (menu_rect.centerx - txt_title.get_width()//2, menu_rect.top + 18))
            pygame.draw.rect(screen, (200, 50, 50), rect_close, border_radius=4); pygame.draw.rect(screen, (240, 200, 50), rect_close, 2, border_radius=4)
            pygame.draw.line(screen, (255,255,255), (rect_close.left+7, rect_close.top+7), (rect_close.right-7, rect_close.bottom-7), 3)
            pygame.draw.line(screen, (255,255,255), (rect_close.right-7, rect_close.top+7), (rect_close.left+7, rect_close.bottom-7), 3)

            def draw_cheat_btn(r, txt):
                pygame.draw.rect(screen, (130, 40, 40), r, border_radius=5); pygame.draw.rect(screen, (220, 180, 50), r, 2, border_radius=5)
                t = font.render(txt, True, (255, 230, 150)); screen.blit(t, (r.centerx - t.get_width()//2, r.centery - t.get_height()//2))

            draw_cheat_btn(btn_boom, "ВЗРЫВ (ЧЕРНОБЫЛЬСКИЙ СЦЕНАРИЙ)")
            draw_cheat_btn(btn_steam, "ПАРОВОЙ ВЗРЫВ")
            draw_cheat_btn(btn_black, "ОТКЛЮЧЕНИЕ СВЕТА (БЛЭКАУТ)")
            draw_cheat_btn(btn_melt, "КИТАЙСКИЙ СИНДРОМ (РАСПЛАВЛЕНИЕ)")
            draw_cheat_btn(btn_xenon, "КСЕНОНОВАЯ ЯМА (ОТРАВЛЕНИЕ)")
            draw_cheat_btn(btn_bearing, "ПЕРЕГРЕВ ПОДШИПНИКОВ ГЦН (>500°C)")
            draw_cheat_btn(btn_shutdown, "ВЫКЛЮЧИТЬ РЕАКТОР (ОСТАНОВ)")
            draw_cheat_btn(btn_startup, "ЗАПУСТИТЬ РЕАКТОР (ПУСК)")
            draw_cheat_btn(btn_hidden, "ПОЛОМКА БЩУ (СКРЫТЫЙ РАЗГОН)")
            draw_cheat_btn(btn_norm, "НОРМАЛЬНАЯ РАБОТА")

    if mag_anim_val > 0.01:
        pygame.draw.rect(screen, (40, 45, 40), mag_panel, border_radius=6)
        pygame.draw.rect(screen, (80, 90, 80), mag_panel, 2, border_radius=6)
        draw_magnetola_button(mag_btn_vol_up, "VOL+", hovers["v_up"])
        draw_magnetola_button(mag_btn_vol_dn, "VOL-", hovers["v_dn"])
        draw_magnetola_button(mag_btn_nxt, ">>", hovers["t_nxt"])
        draw_magnetola_button(mag_btn_prv, "<<", hovers["t_prv"])
        c_col = (50 + hovers["mag_center"]*30, 55 + hovers["mag_center"]*30, 50 + hovers["mag_center"]*30)
        pygame.draw.rect(screen, c_col, mag_btn_mid, border_radius=4)
        pygame.draw.rect(screen, (30, 150, 50), mag_btn_mid, 1, border_radius=4)
        t_name = "НЕ ВЫБРАНО (нажмите)"
        if playlist and 0 <= current_track < len(playlist):
            t_name = os.path.basename(playlist[current_track])
            if len(t_name) > 22: t_name = t_name[:20] + "..."
        t_txt = font_bold.render(t_name, True, (40, 255, 40))
        screen.blit(t_txt, (mag_btn_mid.centerx - t_txt.get_width()//2, mag_btn_mid.centery - 12))
        freq_txt = font_small.render(f"ЧАСТОТА: {88.0 + current_track*0.5:.1f} FM" if playlist else "ЧАСТОТА: --- FM", True, (150, 180, 150))
        screen.blit(freq_txt, (mag_btn_mid.centerx - freq_txt.get_width()//2, mag_btn_mid.centery + 5))

    pygame.draw.rect(screen, (50, 50, 50) if hovers["mag_icon"] < 0.5 else (80, 80, 80), mag_icon_rect, border_radius=5)
    pygame.draw.rect(screen, (200, 200, 200), mag_icon_rect, 2, border_radius=5)
    pygame.draw.circle(screen, (220, 220, 220), (mag_icon_rect.centerx, mag_icon_rect.centery+3), 6)
    pygame.draw.line(screen, (220, 220, 220), (mag_icon_rect.centerx+5, mag_icon_rect.centery+3), (mag_icon_rect.centerx+5, mag_icon_rect.centery-8), 2)
    pygame.draw.line(screen, (220, 220, 220), (mag_icon_rect.centerx+5, mag_icon_rect.centery-8), (mag_icon_rect.centerx+12, mag_icon_rect.centery-4), 2)
# ========== КОНЕЦ ЧАСТИ 13 ==========
# ========== ЧАСТЬ 14: АНИМАЦИЯ ВЗРЫВА И КОНСОЛЬ ==========
    if reactor.explosion_phase > 0 or reactor.console_visible:
        # Если это миссия – сразу показываем консоль без взрывных эффектов
        if reactor.end_type == "mission":
            dim = pygame.Surface((WIDTH, HEIGHT)); dim.set_alpha(200); dim.fill((0,0,0)); screen.blit(dim, (0,0))
            console_rect = pygame.Rect(100, 100, WIDTH - 200, HEIGHT - 200)
            pygame.draw.rect(screen, (0, 30, 0), console_rect, border_radius=5)
            pygame.draw.rect(screen, (0, 255, 0), console_rect, 3, border_radius=5)

            reactor.console_timer += dt
            if reactor.console_progress < len(reactor.console_text):
                if reactor.console_timer > 0.025:
                    reactor.console_progress += 1
                    reactor.console_timer = 0.0
                    if reactor.console_progress % 5 == 0:
                        play_sound('beep')
            displayed_text = reactor.console_text[:reactor.console_progress]
            lines = displayed_text.split('\n')
            y_off = console_rect.y + 20
            for line in lines:
                txt = font.render(line, True, (0, 255, 0))
                screen.blit(txt, (console_rect.x + 20, y_off))
                y_off += 28

            if reactor.console_progress >= len(reactor.console_text):
                draw_soviet_button(rect_restart, "НАЧАТЬ СНАЧАЛА", hovers["restart"])
        else:
            # Стандартный взрыв (оставляем без изменений)
            if reactor.explosion_phase == 1:
                base_shake = reactor.shake_intensity * 8
                boosted_shake = base_shake * reactor.explosion_shake_boost
                if boosted_shake > 0.5:
                    shake_x = random.randint(-int(boosted_shake), int(boosted_shake))
                    shake_y = random.randint(-int(boosted_shake), int(boosted_shake))
                    screen_scroll = pygame.Surface((WIDTH, HEIGHT))
                    screen_scroll.blit(screen, (0, 0))
                    screen.fill((0,0,0))
                    screen.blit(screen_scroll, (shake_x, shake_y))

                flash_power = reactor.flash_intensity * 1.5
                if flash_power > 0.2:
                    flash_alpha = int(flash_power * (120 + 60 * math.sin(current_time * 0.05)))
                    flash_surf = pygame.Surface((WIDTH, HEIGHT))
                    flash_surf.set_alpha(min(255, flash_alpha))
                    flash_surf.fill((255, 255, 200))
                    screen.blit(flash_surf, (0, 0))

                reactor.explosion_timer += dt
                reactor.shake_intensity = min(1.0, reactor.shake_intensity + dt * 2.0)
                reactor.flash_intensity = min(1.0, reactor.flash_intensity + dt * 2.5)

                for p in reactor.explosion_particles[:]:
                    p['x'] += p['vx'] * dt
                    p['y'] += p['vy'] * dt
                    p['vy'] += 40 * dt
                    p['life'] -= dt
                    p['vx'] *= 0.98
                    p['vy'] *= 0.98
                    if p['life'] <= 0:
                        reactor.explosion_particles.remove(p)
                        continue
                    alpha = int(255 * (p['life'] / p['max_life']))
                    if p['type'] == 'spark':
                        color = (p['color'][0], p['color'][1], p['color'][2], alpha)
                    elif p['type'] == 'fire':
                        color = (255, p['color'][1]//2, 0, alpha)
                    elif p['type'] == 'fire2':
                        color = (255, 200, 50, alpha)
                    else:
                        color = (100, 100, 100, alpha//2)
                    surf = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, color, (p['size'], p['size']), p['size'])
                    screen.blit(surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))

                if reactor.explosion_timer < 3.0:
                    radius1 = int(100 + (reactor.explosion_timer / 3.0) * 350)
                    radius2 = int(radius1 * 0.6)
                    alpha1 = int(200 * (1 - reactor.explosion_timer / 3.5))
                    alpha2 = int(255 * (1 - reactor.explosion_timer / 3.5))
                    if alpha1 > 0 and radius1 < 500:
                        surf1 = pygame.Surface((radius1*2+30, radius1*2+30), pygame.SRCALPHA)
                        pygame.draw.circle(surf1, (255, 150, 50, alpha1//2), (radius1+15, radius1+15), radius1)
                        surf2 = pygame.Surface((radius2*2+20, radius2*2+20), pygame.SRCALPHA)
                        pygame.draw.circle(surf2, (255, 255, 200, alpha2), (radius2+10, radius2+10), radius2)
                        surf3 = pygame.Surface((radius2*2+20, radius2*2+20), pygame.SRCALPHA)
                        pygame.draw.circle(surf3, (255, 255, 255, alpha2//2), (radius2+10-20, radius2+10-20), radius2//3)
                        screen.blit(surf1, (WIDTH//2 - radius1 - 15, HEIGHT//2 - radius1 - 15))
                        screen.blit(surf2, (WIDTH//2 - radius2 - 10, HEIGHT//2 - radius2 - 10))
                        screen.blit(surf3, (WIDTH//2 - radius2 - 10, HEIGHT//2 - radius2 - 10))

                if reactor.explosion_timer >= 3.0 or (reactor.end_type == "bearing" and reactor.explosion_timer >= 1.0):
                    reactor.explosion_phase = 2
                    reactor.console_timer = 0.0
                    reactor.console_progress = 0
                    reactor.console_visible = True
                    time_str = f"{int(reactor.shift_timer//3600)+11:02d}:{int((reactor.shift_timer%3600)//60):02d}:{int(reactor.shift_timer%60):02d}"
                    if reactor.end_type == "explosion":
                        reactor.console_text = f"Время смены: {time_str}\nРеактор РБМК Взорвался, немедленная эвакуация г. Припять.\nВоенные и МЧС едут на тушение большого пожара\nна месте взрыва 4 энергоблока ЧАЭС.\n\n26 апреля 1986 года..."
                    elif reactor.end_type == "steam":
                        reactor.console_text = f"Время смены: {time_str}\nПаровой взрыв реактора!\nНемедленная эвакуация г. Припять.\nВоенные и МЧС едут на тушение большого пожара\nна месте взрыва 4 энергоблока ЧАЭС.\n\n26 апреля 1986 года..."
                    elif reactor.end_type == "bearing":
                        reactor.console_text = f"Время смены: {time_str}\nСегодня случилась чрезвычайная ситуация на ЧАЭС.\nВзрыва удалось избежать. Но какой ценой?\nг. Припять останется без света на ближайшие 3-2 недели.\nВы расплавили подшипники и системы ЧАЭС.\nВас ждет высшая мера наказания СССР.\n\n26 апреля 1986 года..."
                    elif reactor.end_type == "melt":
                        reactor.console_text = f"Время смены: {time_str}\nСегодня случилась чрезвычайная ситуация на ЧАЭС.\nВзрыва удалось избежать.\nВы полностью расплавили ядро ЧАЭС.\nРадиоактивное топливо и уран проплавили бетон\nи вошли в землю.\nВы превратили ЧАЭС в большую радиоактивную могилу.\nг. Припять не пострадал.\nУмерли все работники ЧАЭС. Вы в том числе...\n\n26 апреля 1986 года..."
                    elif reactor.end_type == "xenon":
                        reactor.console_text = f"Время смены: {time_str}\nСегодня случилась чрезвычайная ситуация на ЧАЭС.\nВзрыва удалось избежать.\nРабота ЧАЭС остановлена.\nТребуется капитальный ремонт.\nВы никого не убили кроме самой станции.\nг. Припять без света на ближайшие 3-2 дня.\nВы будете наказаны по строжайшей мере СССР.\n\n26 апреля 1986 года..."
                    elif reactor.end_type == "hidden_explosion":
                        reactor.console_text = f"Время смены: {time_str}\nТепловой взрыв реактора. БЩУ уничтожен.\nПриборы зафиксировали неконтролируемый разгон,\nно данные были скрыты из-за ошибки оператора.\n\nВы нарушили базовые правила физики реактора.\n\n26 апреля 1986 года..."
                    else:
                        reactor.console_text = "КОНЕЦ ИГРЫ"

            if reactor.console_visible:
                dim = pygame.Surface((WIDTH, HEIGHT)); dim.set_alpha(200); dim.fill((0,0,0)); screen.blit(dim, (0,0))
                console_rect = pygame.Rect(100, 100, WIDTH - 200, HEIGHT - 200)
                pygame.draw.rect(screen, (0, 30, 0), console_rect, border_radius=5)
                pygame.draw.rect(screen, (0, 255, 0), console_rect, 3, border_radius=5)

                reactor.console_timer += dt
                if reactor.console_progress < len(reactor.console_text):
                    if reactor.console_timer > 0.025:
                        reactor.console_progress += 1
                        reactor.console_timer = 0.0
                        if reactor.console_progress % 5 == 0:
                            play_sound('beep')
                displayed_text = reactor.console_text[:reactor.console_progress]
                lines = displayed_text.split('\n')
                y_off = console_rect.y + 20
                for line in lines:
                    txt = font.render(line, True, (0, 255, 0))
                    screen.blit(txt, (console_rect.x + 20, y_off))
                    y_off += 28

                if reactor.console_progress >= len(reactor.console_text):
                    draw_soviet_button(rect_restart, "НАЧАТЬ СНАЧАЛА", hovers["restart"])
# ========== КОНЕЦ ЧАСТИ 14 ==========
# ========== ЧАСТЬ 15: ЗАВЕРШЕНИЕ (С ОБЫЧНОЙ ТРЯСКОЙ И МИГАНИЕМ) ==========
    if reactor.explosion_phase == 0 and not reactor.console_visible:
        shake_power = reactor.shake_intensity * 8
        if shake_power > 0.3:
            shake_x = random.randint(-int(shake_power), int(shake_power))
            shake_y = random.randint(-int(shake_power), int(shake_power))
            screen_scroll = pygame.Surface((WIDTH, HEIGHT))
            screen_scroll.blit(screen, (0, 0))
            screen.fill((0,0,0))
            screen.blit(screen_scroll, (shake_x, shake_y))

        flash_power = reactor.flash_intensity * 0.7
        if flash_power > 0.2:
            flash_alpha = int(flash_power * (80 + 40 * math.sin(current_time * 0.04)))
            flash_surf = pygame.Surface((WIDTH, HEIGHT))
            flash_surf.set_alpha(min(255, flash_alpha))
            flash_surf.fill((255, 255, 200))
            screen.blit(flash_surf, (0, 0))

    if trans_alpha > 0:
        t_surf = pygame.Surface((WIDTH, HEIGHT)); t_surf.set_alpha(int(trans_alpha)); t_surf.fill((0, 0, 0))
        screen.blit(t_surf, (0, 0))

    pygame.display.flip()
# ========== КОНЕЦ ЧАСТИ 15 ==========
# ========== ЧАСТЬ 18: ЗАВЕРШЕНИЕ ПРОГРАММЫ ==========
pygame.quit()
# ========== КОНЕЦ ЧАСТИ 18 ==========