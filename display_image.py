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

def display_slideshow(image_paths, delay=3, transition="fade", transition_duration=3.0):
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_width, screen_height = screen.get_size()
    clock = pygame.time.Clock()

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

        # Start transition when delay time is reached
        if elapsed >= delay and not is_transitioning:
            is_transitioning = True
            transition_start = current_time
            next_index = (current_index + 1) % len(images)

        # Handle transitions
        if is_transitioning and transition != "none" and len(images) > 1:
            transition_elapsed = current_time - transition_start
            if transition_elapsed < transition_duration:
                progress = transition_elapsed / transition_duration
                if transition == "fade":
                    display_surface = fade_surface(
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
            if sys.argv[3] in ["fade", "slide-left", "slide-right", "slide-up", "slide-down", "none"]:
                transition = sys.argv[3]
                
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