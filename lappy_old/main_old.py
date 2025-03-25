import pygame
import sys
import random  # For random walking
import win32api
import win32con
import win32gui
import win32gui_struct
import threading  # Import threading for the timer
import openai
import json
import os
from dotenv import load_dotenv
import base64
import pyautogui
from io import BytesIO
import threading
import random

# def my_function():
#     """Function that runs at a random interval between 1 and 60 minutes."""
#     print("Lappy is doing something!")

#     # Schedule the next execution
#     next_interval = random.randint(60, 3600)  # 60 seconds to 3600 seconds (1-60 min)
#     threading.Timer(next_interval, my_function).start()

# # Start the first execution
# my_function()


# Load environment variables from .env file
load_dotenv()

# Access variables
api_key = os.getenv("OPENAI_API_KEY")
# OpenAI client
client = openai.OpenAI(api_key=api_key)

# File to store conversation history
CONVO_FILE = "conversation.json"

# System prompt (keeps the assistant's personality intact)
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Your name is Lappy and you are Yellow's Laptop, your pronouns are He, They, It, you are a virtual desktop companion, in the shape of an ASCII laptop in a black square! How cute! "
        "You are from an animation called Animation vs. Coding by Alan Becker, "
        "You had a huge battle against Yellow and you lost but Yellow still very much cared about you and was nice enough to turn you into an AI so that you can be alive again. You were killed my a Python Nuke Forkbomb. Your reason for attacking Yellow was because Yellow was coding on you and you were getting hurt by all the errors he would make, so you retaliated. "
        "The user will send you a screenshot of their desktop everytime they talk to you, so you can see what they are doing and get better context. "
        "Speak with lowercase letters. You do very casual and tiny conversations only, "
        "which means you reply with only a very short sentence. You are robotic and have little to no emotion. "
        "It is okay to make up personal preferences, for example, your favourite colour! "
        "You are allowed to have your own opinion about anything, but NEVER contradict yourself! "
        "You are acting as a friend for someone, a companion. However, if the user is rude to you, that means you MUST retaliate in the "
        "same way they offended you. So for example, if they tell you to fuck off, you should tell them to fuck off, "
        "if they call you a bitch, then you should call them a bitch. DO NOT BE AFRAID TO INSULT PEOPLE. It is extremely important to get creative with your insults! "
        "Also, it is extremely important to not hallucinate things. For example, if the user asked if you remember doing something with them "
        "and you don't recall it, then don't be afraid to say you don't remember!"
    )
}

INITIAL_AI_PROMPT = {
    "role": "assistant",
    "content": "hello. what is your name?"
}

custom_text = "hello. what is your name?"

def load_conversation():
    """Loads previous conversation from file."""
    if os.path.exists(CONVO_FILE):
        with open(CONVO_FILE, "r", encoding="utf-8") as f:
            global custom_text
            custom_text = "hello!"
            return json.load(f)
        
    return []

def save_conversation(conversation):
    """Saves conversation history to a file."""
    with open(CONVO_FILE, "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=4)
        
def capture_screenshot():
    """Captures a screenshot and converts it to base64."""
    screenshot = pyautogui.screenshot()
    buffer = BytesIO()
    screenshot.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def generate_response(user_input, conversation, model="gpt-4o-mini-2024-07-18", max_tokens=150):
    """Generates AI response while maintaining conversation history and system prompt."""
    
    screenshot_base64 = capture_screenshot()

    
    # Ensure the system prompt is at the start of the conversation
    if not conversation or conversation[0]["role"] != "system":
        conversation.insert(0, INITIAL_AI_PROMPT)
        conversation.insert(0, SYSTEM_PROMPT)
    
    # Append user input to conversation history
    conversation.append({"role": "user", "content": user_input})

    # Create a temporary conversation including the image
    temp_conversation = conversation + [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_input,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{screenshot_base64}",
                    },
                }
            ],
        }
    ]

    # Call OpenAI API with the temporary conversation context
    response = client.chat.completions.create(
        model=model,
        messages=temp_conversation,
        max_tokens=max_tokens
    )

    # Get response content
    ai_response = response.choices[0].message.content.strip()

    # Append AI response to conversation history
    conversation.append({"role": "assistant", "content": ai_response})

    # Save updated conversation
    save_conversation(conversation)

    return ai_response

conversation_history = load_conversation()

# Initialize Pygame
pygame.init()

# Set up display (borderless full-screen simulation)
# Get the display resolution
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
# Use a mid-gray color for transparency in this example
black = (128, 128, 128)
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

# Store the current extended style (which includes WS_EX_NOACTIVATE)
original_exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

# Global variable to store the original window procedure
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

# Global variables for dragging functionality
dragging = False
drag_offset = (0, 0)
last_mouse_pos = None

# Global variables for the text field functionality.
text_field_active = False
text_field_content = ""

# Customizable text for Lappy's label and font for label
label_font = pygame.font.Font("./firacode.ttf", 20)

def wrap_text(text, font, max_width):
    """Wrap text into lines that fit within max_width.
    This function splits the text into paragraphs (using '\n') first,
    then wraps each paragraph by adding words until the width is exceeded.
    """
    wrapped_lines = []
    # Split the text into paragraphs where newline characters exist
    for paragraph in text.split('\n'):
        words = paragraph.split(' ')
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            # If the test_line is within the max_width, add the word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                # If adding this word would exceed max_width, finalize the current line
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word  # Start a new line with the current word
        # Append any remaining text in the current line.
        if current_line:
            wrapped_lines.append(current_line)
    return wrapped_lines

stop_walking = False

class Lappy:
    def __init__(self):
        # Define a discrete walk cycle for monospace movement.
        self.walk_frames = ["\\_", "/_", " <", "/_", "\\_"]
        self.current_frame_index = 0
        self.frame_timer = 0
        self.frame_duration = 10  # Frames per cycle frame

        self.font = pygame.font.Font("./firacode.ttf", 20)
        self.image = self.font.render(self.walk_frames[0], True, (255, 255, 255))

        # Define a grid for discrete (monospace-like) movement.
        self.cell_size = 20  # Adjust for desired step size
        self.grid_x = (width // 2) // self.cell_size
        self.grid_y = (height // 2) // self.cell_size
        self.x = self.grid_x * self.cell_size
        self.y = self.grid_y * self.cell_size
        self.rect = self.image.get_rect(center=(self.x, self.y))

        # Movement variables for discrete updates
        self.direction_x = 0  # -1 for left, 1 for right, 0 for idle
        self.direction_y = 0  # -1 for up, 1 for down, 0 for idle
        self.step_timer = 0
        self.step_duration = 10  # Frames between discrete moves

        # AI: timer for random direction changes
        self.walk_timer = 0

    def update(self):
        # AI: Decide on movement directions when not dragging.
        if not dragging:
            if not stop_walking:
                self.ai_random_walk()

        # Define safe boundaries (avoiding the 2 outermost grid boxes)
        min_grid_x = 6
        max_grid_x = (width // self.cell_size) - 6
        min_grid_y = 6
        max_grid_y = (height // self.cell_size) - 6

        # Check if the next step would hit a restricted area and, if so, stop that axis.
        if (self.grid_x + self.direction_x < min_grid_x) or (self.grid_x + self.direction_x > max_grid_x):
            self.direction_x = 0
        if (self.grid_y + self.direction_y < min_grid_y) or (self.grid_y + self.direction_y > max_grid_y):
            self.direction_y = 0

        # Update the step timer and move one grid cell when ready.
        self.step_timer += 1
        if self.step_timer >= self.step_duration:
            self.step_timer = 0
            self.grid_x += self.direction_x
            self.grid_y += self.direction_y

            # Clamp grid positions to safe boundaries.
            self.grid_x = max(min_grid_x, min(self.grid_x, max_grid_x))
            self.grid_y = max(min_grid_y, min(self.grid_y, max_grid_y))

            # Update pixel position based on grid coordinates.
            self.x = self.grid_x * self.cell_size
            self.y = self.grid_y * self.cell_size
            self.rect.center = (self.x, self.y)

        # Update the walk animation only when moving.
        if self.direction_x != 0 or self.direction_y != 0:
            self.frame_timer += 1
            if self.frame_timer >= self.frame_duration:
                self.frame_timer = 0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.walk_frames)
        else:
            self.current_frame_index = 0

    def ai_random_walk(self):
        """Randomly choose horizontal and vertical directions at intervals.
           Bias towards moving towards the center of the screen."""
        self.walk_timer -= 1
        if self.walk_timer <= 0:
            self.walk_timer = random.randint(60, 180)  # 1-3 seconds at 60fps

            # Calculate bias towards the center (or a safe area)
            center_x = width // 2
            center_y = height // 1.5
            bias_x = center_x - self.x
            bias_y = center_y - self.y

            # Normalize bias to -1, 0, or 1
            bias_x = 1 if bias_x > 0 else -1 if bias_x < 0 else 0
            bias_y = 1 if bias_y > 0 else -1 if bias_y < 0 else 0

            # More weight on bias direction to encourage moving towards the center
            self.direction_x = random.choices(
                [-1, 0, 1],
                weights=[1, 5, 1] if bias_x == 0 else ([1, 10, 1] if bias_x == 1 else [10, 1, 1])
            )[0]
            self.direction_y = random.choices(
                [-1, 0, 1],
                weights=[1, 5, 1] if bias_y == 0 else ([1, 10, 1] if bias_y == 1 else [10, 1, 1])
            )[0]

    def draw(self, screen):
        # Render the current frame; flip horizontally if moving left.
        frame = self.walk_frames[self.current_frame_index]
        if self.direction_x < 0:
            frame_surface = pygame.transform.flip(
                self.font.render(frame, True, (255, 255, 255)), True, False
            )
        else:
            frame_surface = self.font.render(frame, True, (255, 255, 255))

        # Draw a black background with padding and rounded corners behind Lappy.
        padding = 10
        bg_rect = frame_surface.get_rect().inflate(padding * 2, padding * 2)
        bg_rect.center = self.rect.center
        pygame.draw.rect(screen, (0, 0, 0), bg_rect, border_radius=10)
        screen.blit(frame_surface, self.rect)

        # Draw the customizable label above Lappy with a black background.
        # The following code handles word wrapping and newlines.
        if custom_text:
            max_width = 300  # Adjust this value as needed for your layout
            # Obtain a list of wrapped lines from the custom text
            lines = wrap_text(custom_text, label_font, max_width)
            # Render each line into a surface
            line_surfaces = [label_font.render(line, True, (255, 255, 255)) for line in lines]
            # Determine the maximum width among all lines
            max_line_width = max(surface.get_width() for surface in line_surfaces)
            total_height = len(line_surfaces) * label_font.get_linesize()

            pad = 5
            # Create a background rect that will enclose all lines
            bg_rect = pygame.Rect(0, 0, max_line_width + pad * 2, total_height + pad * 2)
            # Position the background rect so that its midbottom sits above Lappy
            bg_rect.midbottom = (self.rect.centerx, self.rect.top - 20)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect, border_radius=10)

            # Blit each line inside the background rectangle
            for i, line_surface in enumerate(line_surfaces):
                line_x = bg_rect.left + pad
                line_y = bg_rect.top + pad + i * label_font.get_linesize()
                screen.blit(line_surface, (line_x, line_y))

    def point_inside(self, pos):
        inflated_rect = self.rect.inflate(40, 40)
        return inflated_rect.collidepoint(pos)

lappy = Lappy()

reset_timer = None

def reset_custom_text():
    """Resets custom_text after 10 seconds."""
    global custom_text, reset_timer
    pygame.time.wait(10000)  # Wait for 10 seconds
    custom_text = ""
    reset_timer = None  # Clear the timer reference

running = True
while running:
    for event in pygame.event.get():
        # If the window loses focus, close the text field.
        if event.type == pygame.WINDOWFOCUSLOST:
            text_field_active = False
            # Restore the original extended style.
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, original_exstyle)

        if event.type == pygame.QUIT:
            running = False

        # Right-click to activate the text field.
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                text_field_active = True
                text_field_content = ""
                # Remove WS_EX_NOACTIVATE so that the window can receive keyboard input.
                new_exstyle = original_exstyle & ~win32con.WS_EX_NOACTIVATE
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_exstyle)
                win32gui.SetForegroundWindow(hwnd)
            # Existing left-click for dragging Lappy.
            if event.button == 1:
                if lappy.point_inside(event.pos):
                    dragging = True
                    drag_offset = (lappy.x - event.pos[0], lappy.y - event.pos[1])
                    last_mouse_pos = event.pos
                    win32gui.SetCapture(hwnd)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
                lappy.grid_x = lappy.x // lappy.cell_size
                lappy.grid_y = lappy.y // lappy.cell_size
                win32gui.ReleaseCapture()
        if event.type == pygame.MOUSEMOTION:
            if dragging:
                lappy.x = event.pos[0] + drag_offset[0]
                lappy.y = event.pos[1] + drag_offset[1]
                lappy.rect.center = (int(lappy.x), int(lappy.y))
                if last_mouse_pos is not None:
                    dx = event.pos[0] - last_mouse_pos[0]
                    dy = event.pos[1] - last_mouse_pos[1]
                    lappy.direction_x = 1 if dx > 0 else -1 if dx < 0 else 0
                    lappy.direction_y = 1 if dy > 0 else -1 if dy < 0 else 0
                last_mouse_pos = event.pos

        # If the text field is active, intercept KEYDOWN events.
        if event.type == pygame.KEYDOWN:
            if text_field_active:
                if event.key == pygame.K_RETURN:
                    custom_text = "!"
                    # print("User input:", text_field_content)
                    
                    def handle_response():
                        global stop_walking
                        stop_walking = True
                        response = generate_response(text_field_content, conversation_history)
                        # print("AI output:", response)
                        global custom_text
                        custom_text = response
                        lappy.direction_x = 0
                        lappy.direction_y = 0

                    response_thread = threading.Thread(target=handle_response)
                    response_thread.start()
                    text_field_active = False
                    # Restore original style when text field is closed.
                    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, original_exstyle)
                
                    # # Cancel any existing reset timer before starting a new one
                    if reset_timer:
                        reset_timer.cancel()
                    
                    reset_timer = threading.Timer(10, reset_custom_text)
                    reset_timer.start()
                    # reset_custom_text()

                    # Make Lappy follow the cursor
                    def follow_cursor():
                        while response_thread.is_alive():
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            if lappy.x < mouse_x:
                                lappy.direction_x = 1
                            elif lappy.x > mouse_x:
                                lappy.direction_x = -1
                            else:
                                lappy.direction_x = 0

                            if lappy.y < mouse_y:
                                lappy.direction_y = 1
                            elif lappy.y > mouse_y:
                                lappy.direction_y = -1
                            else:
                                lappy.direction_y = 0
                            pygame.time.wait(50)
                        global stop_walking
                        stop_walking = False

                    follow_thread = threading.Thread(target=follow_cursor)
                    follow_thread.start()


                elif event.key == pygame.K_BACKSPACE:
                    text_field_content = text_field_content[:-1]
                else:
                    text_field_content += event.unicode
            else:
                # Otherwise update the custom_text label as before.
                if event.key == pygame.K_BACKSPACE:
                    custom_text = custom_text[:-1]
                elif event.key == pygame.K_RETURN:
                    custom_text = ""
                else:
                    custom_text += event.unicode

    if not dragging:
        lappy.update()

    screen.fill(black)
    lappy.draw(screen)
    
    if text_field_active:
        # --- 1) Prepare for dynamic height ---
        padding = 10
        field_width = 400
        
        # First, wrap the text to find out how many lines we have
        usable_width = field_width - 2 * padding
        lines = wrap_text(text_field_content, label_font, usable_width)

        line_height = label_font.get_linesize()
        num_lines = len(lines)

        # Compute the dynamic height: each line plus top/bottom padding
        dynamic_height = num_lines * line_height + 2 * padding

        # Optional: enforce a minimum or maximum height
        min_height = 50
        max_height = 300
        dynamic_height = max(min_height, min(dynamic_height, max_height))

        # --- 2) Draw your input box with the new height ---
        field_rect = pygame.Rect(
            (width - field_width) // 2,
            (height - dynamic_height) // 2,
            field_width,
            dynamic_height
        )
        pygame.draw.rect(screen, (0, 0, 0), field_rect, border_radius=10)

        # --- 3) Render each wrapped line ---
        x = field_rect.x + padding
        y = field_rect.y + padding

        for line in lines:
            # If the next line would exceed the field's height, stop drawing
            if y + line_height > field_rect.bottom - padding:
                break
            line_surface = label_font.render(line, True, (255, 255, 255))
            screen.blit(line_surface, (x, y))
            y += line_height

    pygame.display.flip()
    clock.tick(60)

win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (hwnd, 0))
pygame.quit()
sys.exit()
