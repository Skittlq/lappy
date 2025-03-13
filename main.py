import pygame
import sys
import random
import win32api
import win32con
import win32gui
from physics import PhysicsEngine  # Import our physics module
from ball import Ball              # Import our Ball class

# Initialize Pygame
pygame.init()

# Set up display (borderless full-screen simulation)
display_info = pygame.display.Info()
width, height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((width, height), pygame.NOFRAME, display=0)
pygame.display.set_caption('Lappy!')

# Set up the clock for a decent framerate
clock = pygame.time.Clock()

# Get the window handle
hwnd = pygame.display.get_wm_info()["window"]

# Set up layered window and transparency
win32gui.SetWindowLong(
    hwnd,
    win32con.GWL_EXSTYLE,
    win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    | win32con.WS_EX_LAYERED
    | win32con.WS_EX_NOACTIVATE
)
black = (0, 0, 0)
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*black), 0, win32con.LWA_COLORKEY)

# Set window to always be on top
win32gui.SetWindowPos(
    hwnd,
    win32con.HWND_TOPMOST,
    0, 0, 0, 0,
    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
)

# Modify extended style to hide from Alt-Tab and the taskbar
exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
exstyle = (exstyle | win32con.WS_EX_TOOLWINDOW) & ~win32con.WS_EX_APPWINDOW
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, exstyle)

original_exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
oldWndProc = None

def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_COMMAND:
        cmd = win32api.LOWORD(wparam)
        if cmd == 1023:  # ID for our "Exit" menu item
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        return 0
    elif msg == win32con.WM_USER + 20:  # Tray icon callback message
        if lparam == win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, "Exit")
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, hwnd, None)
            win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
        elif lparam == win32con.WM_LBUTTONDBLCLK:
            if win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        return 0
    return win32gui.CallWindowProc(oldWndProc, hwnd, msg, wparam, lparam)

oldWndProc = win32gui.SetWindowLong(hwnd, win32con.GWL_WNDPROC, wnd_proc)

# Create a system tray icon using Shell_NotifyIcon.
hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
nid = (
    hwnd, 0,
    win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
    win32con.WM_USER + 20,
    hicon,
    "Lappy!"
)
win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

# Create a ball and wrap it with the PhysicsEngine
ball = Ball(width // 2, height // 2, 50, (255, 0, 0))
ball_phys = PhysicsEngine(ball, mass=2.0, friction=0.05, gravity=(0, 5000), restitution=0.3)

boundaries = screen.get_rect()

# Variables to track whether the ball is grabbed
ball_grabbed = False
last_mouse_pos = pygame.math.Vector2(0, 0)

running = True
while running:
    dt = clock.tick(60) / 1000  # Convert milliseconds to seconds
    for event in pygame.event.get():
        if event.type == pygame.WINDOWFOCUSLOST:
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, original_exstyle)
        if event.type == pygame.QUIT:
            running = False
        # Check for mouse button events
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                # Check if the mouse is over the ball
                if ball.rect.collidepoint(mouse_pos):
                    ball_grabbed = True
                    # Reset velocity so the physics engine doesn't fight the user's movement
                    ball_phys.velocity = pygame.math.Vector2(0, 0)
                    last_mouse_pos = pygame.math.Vector2(mouse_pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and ball_grabbed:
                # On release, compute a throw velocity based on the mouse's movement
                current_mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
                ball_phys.velocity = (current_mouse_pos - last_mouse_pos) * 5
                ball_grabbed = False

    # Update ball position
    if ball_grabbed:
        current_mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        ball.pos = current_mouse_pos
        ball.update_rect()
        last_mouse_pos = current_mouse_pos
    else:
        ball_phys.update(dt, boundaries)
        ball.pos = pygame.math.Vector2(ball.rect.center)

    # Render the ball
    screen.fill((0, 0, 0))
    ball.draw(screen)
    pygame.display.flip()

win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (hwnd, 0))
pygame.quit()
sys.exit()
