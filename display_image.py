import sys
import pygame
import time

def fade_surface(surface1, surface2, progress):
    """Cross-fade between two surfaces"""
    # Create a new surface with per-pixel alpha
    result = pygame.Surface((surface1.get_width(), surface1.get_height()), pygame.SRCALPHA)
    
    # Fade out first image
    temp1 = surface1.copy()
    temp1.set_alpha(int(255 * (1 - progress)))
    
    # Fade in second image
    temp2 = surface2.copy()
    temp2.set_alpha(int(255 * progress))
    
    # Blit both surfaces
    result.blit(temp1, (0, 0))
    result.blit(temp2, (0, 0))
    
    return result

def slide_surface(surface1, surface2, progress, direction="left"):
    """Slide one surface over another in the specified direction"""
    width = surface1.get_width()
    height = surface1.get_height()
    result = pygame.Surface((width, height))
    result.fill((0, 0, 0))  # Fill with black background
    
    if direction == "slide-left":
        offset = int(width * progress)
        result.blit(surface1, (-offset, 0))
        result.blit(surface2, (width - offset, 0))
    elif direction == "slide-right":
        offset = int(width * progress)
        result.blit(surface1, (offset, 0))
        result.blit(surface2, (-width + offset, 0))
    elif direction == "slide-up":
        offset = int(height * progress)
        result.blit(surface1, (0, -offset))
        result.blit(surface2, (0, height - offset))
    elif direction == "slide-down":
        offset = int(height * progress)
        result.blit(surface1, (0, offset))
        result.blit(surface2, (0, -height + offset))
    
    return result

def zoom_surface(surface1, surface2, progress, zoom_in=True):
    """Zoom transition between two surfaces"""
    width = surface1.get_width()
    height = surface1.get_height()
    result = pygame.Surface((width, height), pygame.SRCALPHA)
    result.fill((0, 0, 0, 255))  # Fully opaque black
    
    if zoom_in:
        # First image zooms in and fades out
        scale = 1 + (progress * 0.3)  # Zoom up to 130%
        scaled_size = (int(width * scale), int(height * scale))
        scaled = pygame.transform.smoothscale(surface1, scaled_size)
        
        # Center the scaled image
        x = (width - scaled_size[0]) // 2
        y = (height - scaled_size[1]) // 2
        
        # Create separate surfaces for alpha blending
        first_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        first_layer.fill((0, 0, 0, 0))  # Transparent
        first_layer.blit(scaled, (x, y))
        first_layer.set_alpha(int(255 * (1 - progress)))
        
        second_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        second_layer.fill((0, 0, 0, 0))  # Transparent
        second_layer.blit(surface2, (0, 0))
        second_layer.set_alpha(int(255 * progress))
        
        result.blit(first_layer, (0, 0))
        result.blit(second_layer, (0, 0))
    else:
        # Second image zooms out from center
        scale = 0.7 + (progress * 0.3)  # Zoom from 70% to 100%
        scaled_size = (int(width * scale), int(height * scale))
        scaled = pygame.transform.smoothscale(surface2, scaled_size)
        
        # Center the scaled image
        x = (width - scaled_size[0]) // 2
        y = (height - scaled_size[1]) // 2
        
        # Create separate surfaces for alpha blending
        first_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        first_layer.fill((0, 0, 0, 0))  # Transparent
        first_layer.blit(surface1, (0, 0))
        first_layer.set_alpha(int(255 * (1 - progress)))
        
        second_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        second_layer.fill((0, 0, 0, 0))  # Transparent
        second_layer.blit(scaled, (x, y))
        second_layer.set_alpha(int(255 * progress))
        
        result.blit(first_layer, (0, 0))
        result.blit(second_layer, (0, 0))
    
    return result

def rotate_surface(surface1, surface2, progress, clockwise=True):
    """Rotate transition between two surfaces"""
    width = surface1.get_width()
    height = surface1.get_height()
    result = pygame.Surface((width, height), pygame.SRCALPHA)
    result.fill((0, 0, 0, 255))
    
    angle = 180 * progress if clockwise else -180 * progress
    
    # Create separate surfaces for rotation and alpha
    rotated1 = pygame.transform.rotozoom(surface1, angle, 1)
    rotated2 = pygame.transform.rotozoom(surface2, angle - 180 if clockwise else angle + 180, 1)
    
    # Create alpha layers
    first_layer = pygame.Surface((width, height), pygame.SRCALPHA)
    first_layer.fill((0, 0, 0, 0))
    x1 = (width - rotated1.get_width()) // 2
    y1 = (height - rotated1.get_height()) // 2
    first_layer.blit(rotated1, (x1, y1))
    first_layer.set_alpha(int(255 * (1 - progress)))
    
    second_layer = pygame.Surface((width, height), pygame.SRCALPHA)
    second_layer.fill((0, 0, 0, 0))
    x2 = (width - rotated2.get_width()) // 2
    y2 = (height - rotated2.get_height()) // 2
    second_layer.blit(rotated2, (x2, y2))
    second_layer.set_alpha(int(255 * progress))
    
    result.blit(first_layer, (0, 0))
    result.blit(second_layer, (0, 0))
    
    return result

def fade_to_black(surface1, surface2, progress):
    """Fade first image to black, then fade in second image"""
    width = surface1.get_width()
    height = surface1.get_height()
    result = pygame.Surface((width, height))
    result.fill((0, 0, 0))  # Black background
    
    if progress < 0.5:
        # First half: fade out first image to black
        temp = surface1.copy()
        temp.set_alpha(int(255 * (1 - progress * 2)))
        result.blit(temp, (0, 0))
    else:
        # Second half: fade in second image from black
        temp = surface2.copy()
        temp.set_alpha(int(255 * ((progress - 0.5) * 2)))
        result.blit(temp, (0, 0))
    
    return result

def display_slideshow(image_paths, delay=3, transition="fade", transition_duration=3.0):
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_width, screen_height = screen.get_size()
    clock = pygame.time.Clock()

    # Hide the mouse cursor
    pygame.mouse.set_visible(False)

    # Debug output
    print(f"Screen size: {screen_width}x{screen_height}")
    print(f"Loading {len(image_paths)} images...")
    print(f"Settings: delay={delay}, transition={transition}, transition_duration={transition_duration}")

    # Load and scale all images
    images = []
    for path in image_paths:
        try:
            print(f"Loading image: {path}")
            img = pygame.image.load(path)
            print(f"Original size: {img.get_width()}x{img.get_height()}")
            
            # Calculate aspect ratio preserving scale
            img_width = img.get_width()
            img_height = img.get_height()
            aspect_ratio = img_width / img_height
            
            if screen_width / screen_height > aspect_ratio:
                new_height = screen_height
                new_width = int(new_height * aspect_ratio)
            else:
                new_width = screen_width
                new_height = int(new_width / aspect_ratio)
            
            scaled_img = pygame.transform.scale(img, (new_width, new_height))
            print(f"Scaled size: {new_width}x{new_height}")
            
            # Center the image on a black background
            display_surface = pygame.Surface((screen_width, screen_height))
            display_surface.fill((0, 0, 0))
            x = (screen_width - new_width) // 2
            y = (screen_height - new_height) // 2
            display_surface.blit(scaled_img, (x, y))
            images.append(display_surface)
            print(f"Successfully loaded and scaled image: {path}")
        except Exception as e:
            print(f"Error loading image {path}: {e}")

    if not images:
        print("No images were successfully loaded!")
        pygame.quit()
        return

    print(f"Successfully loaded {len(images)} images")
    
    current_index = 0
    next_index = 1 if len(images) > 1 else 0
    last_switch = time.time()
    is_transitioning = False
    transition_start = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                running = False
                pygame.quit()
                return

        current_time = time.time()
        elapsed = current_time - last_switch

        # For "none" transition, just switch immediately when delay is reached
        if transition == "none":
            if elapsed >= delay:
                current_index = (current_index + 1) % len(images)
                last_switch = current_time
                display_surface = images[current_index]
        else:
            # Start transition when delay time is reached
            if elapsed >= delay and not is_transitioning:
                is_transitioning = True
                transition_start = current_time
                next_index = (current_index + 1) % len(images)

            # Handle transitions
            if is_transitioning and len(images) > 1:
                transition_elapsed = current_time - transition_start
                if transition_elapsed < transition_duration:
                    progress = transition_elapsed / transition_duration
                    if transition == "fade":
                        display_surface = fade_surface(
                            images[current_index],
                            images[next_index],
                            progress
                        )
                    elif transition == "fade-black":
                        display_surface = fade_to_black(
                            images[current_index],
                            images[next_index],
                            progress
                        )
                    elif transition.startswith("slide-"):
                        display_surface = slide_surface(
                            images[current_index],
                            images[next_index],
                            progress,
                            direction=transition
                        )
                    elif transition == "zoom-in":
                        display_surface = zoom_surface(
                            images[current_index],
                            images[next_index],
                            progress,
                            zoom_in=True
                        )
                    elif transition == "zoom-out":
                        display_surface = zoom_surface(
                            images[current_index],
                            images[next_index],
                            progress,
                            zoom_in=False
                        )
                    elif transition == "rotate-cw":
                        display_surface = rotate_surface(
                            images[current_index],
                            images[next_index],
                            progress,
                            clockwise=True
                        )
                    elif transition == "rotate-ccw":
                        display_surface = rotate_surface(
                            images[current_index],
                            images[next_index],
                            progress,
                            clockwise=False
                        )
                else:
                    # Transition complete
                    current_index = next_index
                    is_transitioning = False
                    last_switch = current_time
                    display_surface = images[current_index]
            else:
                display_surface = images[current_index]

        screen.fill((0, 0, 0))
        screen.blit(display_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # Show the cursor again before quitting
    pygame.mouse.set_visible(True)
    pygame.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_paths = [path.strip() for path in sys.argv[1].split(',') if path.strip()]
        delay = 10  # default delay
        transition = "fade"  # default transition
        transition_duration = 3.0  # default transition duration
        
        # Debug the image paths and arguments
        print(f"Received image paths: {image_paths}")
        print(f"Received arguments: {sys.argv}")
        
        # Process remaining arguments in order
        if len(sys.argv) > 2:  # Delay
            try:
                delay = float(sys.argv[2])
            except ValueError:
                print(f"Invalid delay value: {sys.argv[2]}, using default")
                
        if len(sys.argv) > 3:  # Transition type
            valid_transitions = [
                "fade", "fade-black", "slide-left", "slide-right", "slide-up", "slide-down",
                "zoom-in", "zoom-out", "rotate-cw", "rotate-ccw", "none"
            ]
            if sys.argv[3] in valid_transitions:
                transition = sys.argv[3]
            else:
                print(f"Invalid transition type: {sys.argv[3]}, using default")
                
        if len(sys.argv) > 4:  # Transition duration
            try:
                transition_duration = float(sys.argv[4])
            except ValueError:
                print(f"Invalid transition duration: {sys.argv[4]}, using default")
        
        if len(image_paths) < 1:
            print("Error: No valid image paths provided")
            sys.exit(1)
            
        print(f"Running with: delay={delay}, transition={transition}, transition_duration={transition_duration}")
        display_slideshow(image_paths, delay, transition, transition_duration) 