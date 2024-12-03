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
    """Zoom transition with scale caching"""
    width = surface1.get_width()
    height = surface1.get_height()
    result = pygame.Surface((width, height), pygame.SRCALPHA)
    result.fill((0, 0, 0, 255))
    
    if zoom_in:
        scale = 1 + (progress * 0.3)
        scaled_size = (int(width * scale), int(height * scale))
        
        # Cache scaled surface
        cache_key = (id(surface1), scaled_size)
        if not hasattr(zoom_surface, 'cache'):
            zoom_surface.cache = {}
        
        if cache_key not in zoom_surface.cache:
            zoom_surface.cache[cache_key] = pygame.transform.smoothscale(surface1, scaled_size)
        
        scaled = zoom_surface.cache[cache_key]
        
        # Create separate surfaces for alpha blending
        first_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        first_layer.fill((0, 0, 0, 0))  # Transparent
        first_layer.blit(scaled, (0, 0))
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
    """Rotate transition between two surfaces with caching"""
    width = surface1.get_width()
    height = surface1.get_height()
    result = pygame.Surface((width, height), pygame.SRCALPHA)
    result.fill((0, 0, 0, 255))
    
    # Cache key based on angle
    angle = 180 * progress if clockwise else -180 * progress
    cache_key1 = (id(surface1), angle)
    cache_key2 = (id(surface2), angle - 180 if clockwise else angle + 180)
    
    # Use cached rotated surfaces if available
    if not hasattr(rotate_surface, 'cache'):
        rotate_surface.cache = {}
    
    if cache_key1 not in rotate_surface.cache:
        rotate_surface.cache[cache_key1] = pygame.transform.rotozoom(surface1, angle, 1)
    if cache_key2 not in rotate_surface.cache:
        rotate_surface.cache[cache_key2] = pygame.transform.rotozoom(surface2, angle - 180 if clockwise else angle + 180, 1)
    
    rotated1 = rotate_surface.cache[cache_key1]
    rotated2 = rotate_surface.cache[cache_key2]
    
    # Clear cache periodically to prevent memory growth
    if len(rotate_surface.cache) > 360:  # Clear after full rotation worth of angles
        rotate_surface.cache.clear()
    
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

def load_and_scale_image(path, screen_width, screen_height):
    """Load and scale image with error handling"""
    try:
        img = pygame.image.load(path).convert()  # Convert for faster blitting
        img_width = img.get_width()
        img_height = img.get_height()
        aspect_ratio = img_width / img_height
        
        if screen_width / screen_height > aspect_ratio:
            new_height = screen_height
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = screen_width
            new_height = int(new_width / aspect_ratio)
        
        scaled_img = pygame.transform.smoothscale(img, (new_width, new_height))
        
        # Create display surface
        display_surface = pygame.Surface((screen_width, screen_height))
        display_surface.fill((0, 0, 0))
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
        display_surface.blit(scaled_img, (x, y))
        
        return display_surface
    except Exception as e:
        print(f"Error loading image {path}: {e}")
        return None

def display_slideshow(image_paths, delay=3, transition="fade", transition_duration=3.0):
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_width, screen_height = screen.get_size()
    clock = pygame.time.Clock()

    # Hide the mouse cursor
    pygame.mouse.set_visible(False)

    # Load and setup logo for loading animation
    try:
        logo = pygame.image.load('logo_white.png').convert_alpha()
        # Scale logo to 1/3 screen height maintaining aspect ratio
        logo_height = screen_height // 4
        aspect_ratio = logo.get_width() / logo.get_height()
        logo_width = int(logo_height * aspect_ratio)
        logo = pygame.transform.smoothscale(logo, (logo_width, logo_height))
        
        # Position logo at screen center
        logo_x = (screen_width - logo_width) // 2
        logo_y = (screen_height - logo_height) // 2
        
        # Function to draw loading progress
        def draw_loading_progress(progress):
            fill_height = int(logo_height * progress)
            
            # Create a mask for the "filling" effect
            mask = pygame.Surface((logo_width, logo_height), pygame.SRCALPHA)
            mask.fill((255, 255, 255, 0))  # Transparent
            
            # Fill from bottom to top
            visible_portion = pygame.Rect(0, logo_height - fill_height, logo_width, fill_height)
            mask.fill((255, 255, 255, 255), visible_portion)  # Opaque
            
            # Apply mask to logo
            frame = logo.copy()
            frame.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Draw frame
            screen.fill((0, 0, 0))
            screen.blit(frame, (logo_x, logo_y))
            pygame.display.flip()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    pygame.quit()
                    return True
            return False

        # Show initial empty logo
        draw_loading_progress(0)
        
        # Debug output
        print(f"Screen size: {screen_width}x{screen_height}")
        print(f"Loading {len(image_paths)} images...")
        print(f"Settings: delay={delay}, transition={transition}, transition_duration={transition_duration}")

        # Load and scale all images with progress
        images = []
        total_images = len(image_paths)
        
        for i, path in enumerate(image_paths):
            try:
                print(f"Loading image: {path}")
                img = load_and_scale_image(path, screen_width, screen_height)
                if img:
                    images.append(img)
                    print(f"Successfully loaded image: {path}")
                
                # Update loading progress
                progress = (i + 1) / total_images
                if draw_loading_progress(progress):
                    return  # Exit if requested
                
                clock.tick(60)  # Keep animation smooth
                
            except Exception as e:
                print(f"Error loading image {path}: {e}")

        # Fade out the logo to black
        fade_duration = 0.5  # Half second fade out
        fade_start = time.time()
        while time.time() - fade_start < fade_duration:
            progress = (time.time() - fade_start) / fade_duration
            
            # Create fading logo
            frame = logo.copy()
            frame.set_alpha(int(255 * (1 - progress)))
            
            # Draw frame
            screen.fill((0, 0, 0))
            screen.blit(frame, (logo_x, logo_y))
            pygame.display.flip()
            clock.tick(60)
            
            # Check for early exit
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    pygame.quit()
                    return

        # Ensure we end on black
        screen.fill((0, 0, 0))
        pygame.display.flip()
        
        # Small pause on black screen
        time.sleep(0.2)

    except Exception as e:
        print(f"Error loading logo: {e}")
        # Fallback to simple loading text
        font = pygame.font.SysFont(None, 48)
        loading_text = font.render("Loading...", True, (255, 255, 255))
        text_rect = loading_text.get_rect(center=(screen_width/2, screen_height/2))
        screen.fill((0, 0, 0))
        screen.blit(loading_text, text_rect)
        pygame.display.flip()
        
        # Load images without visual progress
        images = []
        for path in image_paths:
            try:
                img = load_and_scale_image(path, screen_width, screen_height)
                if img:
                    images.append(img)
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
    display_surface = pygame.Surface((screen_width, screen_height))
    display_surface.fill((0, 0, 0))

    # Initial fade in from black
    fade_start = time.time()
    while time.time() - fade_start < transition_duration:
        progress = (time.time() - fade_start) / transition_duration
        temp = images[current_index].copy()
        temp.set_alpha(int(255 * progress))
        
        screen.fill((0, 0, 0))
        screen.blit(temp, (0, 0))
        pygame.display.flip()
        clock.tick(60)

        # Check for early exit
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                pygame.quit()
                return

    display_surface = images[current_index].copy()
    last_switch = time.time()  # Reset timer after initial fade

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
                display_surface = images[current_index].copy()
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
                    display_surface = images[current_index].copy()
            else:
                display_surface = images[current_index].copy()

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