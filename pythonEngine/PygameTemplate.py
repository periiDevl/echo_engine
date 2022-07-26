import pygame
import os
import random
pygame.font.init()

WIDTH, HEIGHT = 16*100, 9*100
WIN = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Scene")
exitNum = 0


HEALTH_FONT = pygame.font.SysFont('comicsans', 40)
WINNER_FONT = pygame.font.SysFont('comicsans', 100)

FPS = 60

SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 55, 40

background = pygame.image.load(os.path.join("2dEngineAssets", 'space.png'))
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
                       
def drawWin(red, yellow, rbullets, ybullets, red_health, yellow_health):
     WIN.blit(background, (0, 0))
     WIN.blit(yellowSpaceship, (yellow.x, yellow.y))
     WIN.blit(redSpaceship, (red.x, red.y))
     
     red_health_text = HEALTH_FONT.render("Health: " + str(red_health), 1, "#FFFFFF")
     yellow_health_text = HEALTH_FONT.render("Health: " + str(yellow_health), 1, "#FFFFFF")
     WIN.blit(red_health_text, (WIDTH - red_health_text.get_width() -10, 10))
     WIN.blit(yellow_health_text, (10, 10))
         
     for bullet in rbullets:
          pygame.draw.rect(WIN, "#ff0000", bullet)
     for bullet in ybullets:
          pygame.draw.rect(WIN, "#cfac00", bullet)
          
     pygame.display.update()

yellowSpaceshipSprite = pygame.image.load(os.path.join("2dEngineAssets", 'spaceship.png'))
yellowSpaceship = pygame.transform.rotate(pygame.transform.scale(yellowSpaceshipSprite, (SPACESHIP_WIDTH,SPACESHIP_HEIGHT)), 90)

redSpaceshipSprite = pygame.image.load(os.path.join("2dEngineAssets", 'spaceship.png'))
redSpaceship = pygame.transform.rotate(pygame.transform.scale(redSpaceshipSprite, (SPACESHIP_WIDTH,SPACESHIP_HEIGHT)), -90)

RedHit = pygame.USEREVENT + 1
YellowHit = pygame.USEREVENT + 2
RedAdd = pygame.USEREVENT + 1
YellowAdd = pygame.USEREVENT + 2

VEL = 6
MaxBullets = 5
bulletVel = 12
def yellowMovement(yellow, keyspressed):
     if keyspressed[pygame.K_a] and yellow.x - VEL > 0:
          yellow.x -= VEL
     if keyspressed[pygame.K_d] and yellow.x + VEL + yellow.width < 1600/2:
          yellow.x += VEL
     if keyspressed[pygame.K_w] and yellow.y - VEL > 0:
          yellow.y -= VEL
     if keyspressed[pygame.K_s] and yellow.y + VEL + yellow.width < 900:
          yellow.y += VEL
def redMovement(red, keyspressed):
     if keyspressed[pygame.K_LEFT] and red.x - VEL > WIDTH/2:
          red.x -= VEL
     if keyspressed[pygame.K_RIGHT] and red.x + VEL + red.width < 1600:
          red.x += VEL
     if keyspressed[pygame.K_UP] and red.y - VEL > 0:
          red.y -= VEL
     if keyspressed[pygame.K_DOWN] and red.y + VEL + red.width < 900:
          red.y += VEL
def handleBullets(red, yellow ,RedShot, YellowShot, red_bullets,yellow_bullets):
     if RedShot and len(red_bullets) < MaxBullets:
          bullet = pygame.Rect(red.x, red.y + red.height//2 - 2, 10 , 5)
          red_bullets.append(bullet)
     
     if YellowShot and len(yellow_bullets) < MaxBullets:
          bullet = pygame.Rect(yellow.x, yellow.y + yellow.height//2 - 2, 10 , 5)
          yellow_bullets.append(bullet)

     for b in yellow_bullets:
          b.x += bulletVel
          if red.colliderect(b) or  b.x > WIDTH + b.width or b.x < 0:
               pygame.event.post(pygame.event.Event(RedHit))
               yellow_bullets.remove(b)
     for b in red_bullets:
          b.x -= bulletVel
          if yellow.colliderect(b) or  b.x > WIDTH + b.width or b.x < 0:
               if yellow.colliderect(b):
                    pygame.event.post(pygame.event.Event(YellowHit))
                    red_bullets.remove(b)

     for RedB in red_bullets:
          for YellowB in yellow_bullets:
               if YellowB.colliderrect(RedB):
                    yellow_bullets.remove(YellowB)
                    red_bullets.remove(RedB)
def main():
     red = pygame.Rect(WIDTH-55, 300, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)
     yellow = pygame.Rect(0, 300, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)

     yellow_bullets =[]
     red_bullets =[]

     RedHealth = 10
     YellowHealth = 10
          
     clock = pygame.time.Clock()
     run = True
     while run:
          YellowShot = False
          RedShot = False
          clock.tick(FPS)
          for event in pygame.event.get():
               if event.type == pygame.QUIT:
                    global exitNum
                    
                    if exitNum == 1:
                         run = False
                    else:
                         print("Close window?")
                    exitNum += 1
               if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LSHIFT:
                         YellowShot = True
                    if event.key == pygame.K_RSHIFT:
                         RedShot = True
                         
               if event.type == YellowHit:
                    if random.randrange(1, 101) > 75:
                         YellowHealth += 1
                    else:
                         YellowHealth -= 1
               if event.type == RedHit:
                    if random.randrange(1, 101) > 75:
                         RedHealth += 1
                    else:
                         RedHealth -= 1
          WinText = ""
          
          if RedHealth <= 0:
               WinText = "Yellow won"
               run = False
          if YellowHealth <= 0:
               WinText = "Red won"
               run = False
          if WinText != "":
               print(WinText)
          
          keyspressed = pygame.key.get_pressed()
          yellowMovement(yellow, keyspressed)
          redMovement(red, keyspressed)
          handleBullets(red, yellow, RedShot,YellowShot, red_bullets,yellow_bullets)
                    
          drawWin(red, yellow ,red_bullets,yellow_bullets, RedHealth,YellowHealth)
          

     pygame.quit()

if __name__ == "__main__":
     main()
