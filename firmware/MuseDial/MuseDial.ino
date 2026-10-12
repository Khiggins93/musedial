// Local, offline Blender-prerendered avatar on M5Stack Dial.
// Hardware: https://docs.m5stack.com/en/core/Dial
// Vendor drivers: M5Dial 1.0.3, M5Unified 0.2.25, M5GFX 0.2.32.
// Independent community firmware. See NOTICE and docs/ASSETS.md.
#include <M5Dial.h>
#include <esp_system.h>
#include <math.h>
#include "avatar_frames.h"
#include "halloween_assets.h"
#include "button_actions.h"
#include "play_effects.h"
#include "companion.h"
#include "companion_frames.h"
#include "life.h"
#include "life_tests.h"

static constexpr int SCREEN = 240;
static constexpr int AVATAR = 192;
static constexpr int ORIGIN = (SCREEN - AVATAR) / 2;
static constexpr uint32_t FRAME_MS = 50;
static constexpr char VERSION[] = "3.3.0-life";
static Life life;
static PlayEffects play;
static Companion companion;
static M5Canvas canvas(&M5Dial.Display);
static uint32_t decodeErrors = 0;
static int activeClip = 0;
static HalloweenAssets halloweenAssets;
static ButtonActions buttonActions;
static bool halloween = false;
static bool temporarySelection = false;
static uint32_t selectionSince = 0;

// These are visual expressions only: no microphone, speaker or network is used.
static constexpr uint32_t ACCENTS[] = {0xa77dff,0x5cb8ff,0xe07bff,0x6ff0bf,0x7c72d0,0xa77dff,0xa77dff,0x5cb8ff,0x7c72d0};
static constexpr const char* LABELS[] = {
    "TRANQUILO", "CURIOSO", "PENSANDO", "ANIMADO", "DORMILON", "FELIZ", "SALUDO", "SORPRESA", "SUENO"
};
static constexpr int MOODS = sizeof(ACCENTS) / sizeof(ACCENTS[0]);
static constexpr const char* HALLOWEEN_LABELS[] = {
    "TRANQUILO", "CURIOSO", "TRAVIESO", "SALUDO", "RISITA", "SORPRESA",
    "BOO", "CARCAJADA", "BAILE", "HECHIZO", "DORMILON", "BOSTEZO"
};
static int moodCount() { return halloween ? 12 : MOODS; }
static const char* moodLabel(int i) { return halloween ? HALLOWEEN_LABELS[i] : LABELS[i]; }
static int mood = 0;
static bool automatic = true;
static bool sleeping = false;
static bool wakeProtection = false;
static uint32_t lastWakeAt = 0;
static bool displayReady = false;
static uint8_t brightness = 150;
static uint32_t modeSince = 0, lastFrame = 0, lastStatus = 0;
static uint32_t petSince = 0, hintUntil = 7000, frameCount = 0;
static uint32_t touchCount = 0, buttonCount = 0, encoderCount = 0;
static uint32_t maxFrameUs = 0;
static bool petted = false;
static long encoderBase = 0;
static char command[80];
static size_t commandLen = 0;
static bool commandOverflow = false;

static void showHint() { hintUntil = millis() + 2500; }

static bool dreaming() {
    return !sleeping && !petted && !play.casting
        && (halloween ? (mood==10 || mood==11)
                      : (!companion.active() && (mood==4 || mood==8)));
}

// Six staggered Z sprites rise beside the hood, inside the circular display.
// Reuse the existing canvas: no extra buffers, fonts or allocations.
static void drawDreams(uint32_t elapsed) {
    for(unsigned i=0;i<6;++i) {
        float t=((elapsed%3000+i*500)%3000)/3000.0f;
        float fade=fminf(1.0f,fminf(t*8.0f,(1.0f-t)*4.0f));
        if(fade<.02f)continue;
        int x=174+lroundf(12*t+3*sinf(t*6.2831853f));
        int y=103-lroundf(64*t), size=5+lroundf(4*t);
        uint16_t ink=canvas.color565(lroundf((halloween?212:165)*fade),
                                     lroundf((halloween?144:180)*fade),255*fade);
        canvas.drawFastHLine(x,y,size,ink);
        canvas.drawFastHLine(x,y+size-1,size,ink);
        canvas.drawLine(x+size-1,y,x,y+size-1,ink);
        if(size>=7)canvas.drawLine(x+size-2,y,x,y+size-2,ink);
    }
}

static void setMood(int next) {
    play.clear(); companion.clear();
    mood = ((next % moodCount()) + moodCount()) % moodCount();
    petted = false;
    modeSince = millis();
    showHint();
}

static void startAutomatic() {
    automatic = true; temporarySelection = false;
    life.start(millis(), esp_random()); showHint();
}

static bool interact(bool greet = true) {
    return life.interact(millis(), esp_random(), greet);
}

static bool wakeCharacter() {
    if(!life.asleep()) return false;
    interact(); wakeProtection = true; lastWakeAt = millis();
    return true;
}

static bool setTheme(bool value) {
    if (value && !halloweenAssets.data) return false;
    halloween = value; petted = false; temporarySelection = false;
    automatic = true; activeClip = 0;
    setSleeping(false); setMood(0);
    life = Life{}; life.halloween = halloween; startAutomatic();
    return true;
}

static void selectMood(int next) {
    automatic = false; setMood(next);
    life.manual(millis());
    temporarySelection = halloween; selectionSince = millis();
}

static void setSleeping(bool value) {
    interact(false);
    if(value) { play.clear(); companion.clear(); petted=false; }
    if(sleeping && !value) {
        wakeProtection=true;lastWakeAt=millis();
        if(automatic)startAutomatic();
    }
    life.touching = life.consumeTouch = false;
    sleeping = value;
    M5Dial.Display.setBrightness(value ? 0 : brightness);
    if (!value) { modeSince = millis(); showHint(); }
}

static void pet() {
    if (sleeping) setSleeping(false);
    if(wakeCharacter())return;
    interact();
    if(!halloween) { companion.pet(millis()); modeSince=millis(); return; }
    petted = true;
    petSince = millis();
    if(halloween)play.touch(petSince);
}

static void turnWheel(int steps) {
    if(sleeping)setSleeping(false);
    interact(false);
    if(play.casting)return;
    if(halloween && mood==9) {
        play.turn((unsigned)abs(steps),millis());
        temporarySelection=true; selectionSince=millis(); automatic=false; showHint();
        life.manual(millis());
    } else selectMood(mood+(steps % moodCount()));
}

static void clickButton() {
    if(wakeCharacter())return;
    interact();
    if(play.casting)return;
    if(halloween && play.charge) {
        if(play.cast(millis())) { petted=false; startAutomatic(); modeSince=millis(); }
        showHint();return;
    }
    automatic=!automatic;temporarySelection=false;modeSince=millis();showHint();
    if(automatic)startAutomatic();else life.manual(millis());
}

// Shared by physical touch and USB. The complete wake contact is consumed.
static void touchDown(int x, int y) {
    if(sleeping)setSleeping(false);
    bool wasTouching = life.touching;
    if(life.down(millis(),esp_random())) {
        wakeProtection=true; lastWakeAt=millis(); return;
    }
    if(wakeProtection && life.state==Life::Greeting) {
        life.consumeTouch=true; return;
    }
    if(halloween) { if(!wasTouching)pet(); }
    else { companion.down(millis(),x,y); modeSince=millis(); }
}

static void touchUp() {
    if(!life.touching)return;
    if(!life.up(millis(),esp_random()) && !halloween) {
        companion.up(millis()); modeSince=millis();
    }
}

static void status() {
    companion.update(millis());
    Serial.printf("{\"firmware\":\"MuseDial\",\"version\":\"%s\","
                  "\"board\":\"M5Stack Dial\",\"detected_dial\":%s,"
                  "\"display_ready\":%s,\"width\":%d,\"height\":%d,"
                  "\"flash_bytes\":%u,\"psram_bytes\":%u,"
                  "\"free_heap\":%u,\"min_heap\":%u,\"uptime_ms\":%u,"
                  "\"frames\":%u,\"max_frame_us\":%u,\"mood\":%d,"
                  "\"automatic\":%s,\"sleeping\":%s,\"brightness\":%u,"
                  "\"touch_events\":%u,\"button_events\":%u,\"encoder_steps\":%u,"
                  "\"active_clip\":%d,\"animation\":\"%s\",\"decode_errors\":%u,"
                  "\"theme\":\"%s\",\"halloween_ready\":%s,\"asset_error\":\"%s\","
                  "\"bats_active\":%s,\"bats_count\":%d,\"temporary_selection\":%s,"
                  "\"magic_charge\":%u,\"casting\":%s,\"tickled\":%s,"
                  "\"dreaming\":%s,\"companion\":\"%s\",\"affection\":%u,\"gaze_x\":%d,\"gaze_y\":%d,"
                  "\"life_state\":\"%s\",\"idle_ms\":%u,\"spontaneous_active\":%s,"
                  "\"network\":\"disabled\",\"audio\":\"disabled\"}\n",
                  VERSION, M5Dial.Display.getBoard() == m5::board_t::board_M5Dial ? "true" : "false",
                  displayReady ? "true" : "false", M5Dial.Display.width(), M5Dial.Display.height(),
                  ESP.getFlashChipSize(), ESP.getPsramSize(), ESP.getFreeHeap(),
                  ESP.getMinFreeHeap(), millis(), frameCount, maxFrameUs, mood,
                  automatic ? "true" : "false", sleeping ? "true" : "false", brightness,
                  touchCount, buttonCount, encoderCount, activeClip, moodLabel(activeClip), decodeErrors,
                  halloween ? "halloween" : "normal", halloweenAssets.data ? "true" : "false",
                  halloweenAssets.error ? halloweenAssets.error : "none",
                  halloween && petted ? "true" : "false", halloween && petted ? 4 : 0,
                  temporarySelection ? "true" : "false",play.charge,
                  play.casting ? "true" : "false",play.tickled ? "true" : "false",
                  dreaming() ? "true" : "false", companion.label(), companion.affection, companion.gazeX, companion.gazeY,
                  life.label(sleeping),life.idle(millis()),life.spontaneous ? "true" : "false");
}

// Three wing poses; silhouettes are rendered without allocation each frame.
static const char BAT[3][9][20] = {
 {"##               ##","###             ###","####    # #    ####","#####   ###   #####","  ##### ### #####  ","    ###########    ","     ## ### ##     ","        ###        ","         #         "},
 {"                   ","        # #        ","###     ###     ###"," ####   ###   #### ","  ###############  ","   #############   ","    ##  ###  ##    ","        ###        ","         #         "},
 {"                   ","        # #        ","        ###        ","   ##   ###   ##   ","  ###############  "," ###############   ","####    ###    ####","###     ###     ###","##       #       ##"}
};
static void drawBats(uint32_t elapsed,int frame) {
    for(int i=0;i<4;i++) {
        float phase=elapsed*(play.tickled ? .0042f : .0019f)+i*1.5707963f;
        int cx=120+lroundf((play.tickled ? 74+8*sinf(elapsed*.007f+i) : 82)*cosf(phase));
        int cy=125+lroundf(37*sinf(phase)+(play.tickled ? 12*sinf(phase*3+i) : 0));
        bool rear=sinf(phase)<0;
        int wing=(elapsed/110+i)%3;
        uint16_t color=canvas.color565(rear?110:175,rear?52:95,rear?160:245);
        for(int y=0;y<9;y++)for(int x=0;x<19;x++)if(BAT[wing][y][x]=='#') {
            int px=cx+x-9,py=cy+y-4;
            if(rear && halloweenAssets.covers(frame,px-ORIGIN,py-ORIGIN))continue;
            canvas.drawPixel(px,py,color);
        }
    }
}

static void drawMagic(uint32_t now) {
    if(!play.charge && !play.casting)return;
    float t=(now-(play.casting ? play.castAt : play.chargedAt))*.001f;
    uint16_t gold=canvas.color565(255,190,65),violet=canvas.color565(190,120,255);
    int count=play.casting ? 24 : play.charge*2;
    for(int i=0;i<count;i++) {
        float angle=i*2.39996f+t*(play.casting ? 2.5f : 1.3f);
        float radius=play.casting ? 45+40*(.5f+.5f*sinf(t*2+i)) : 68+play.charge*2;
        int x=120+lroundf(radius*cosf(angle)), y=126+lroundf(radius*.75f*sinf(angle));
        canvas.drawFastHLine(x-2,y,5,i%2 ? gold : violet);
        canvas.drawFastVLine(x,y-2,5,i%2 ? gold : violet);
    }
    if(play.casting)for(int i=0;i<3;i++) {
        float a=t*1.8f+i*2.0944f;
        int x=120+lroundf(87*cosf(a)),y=120+lroundf(65*sinf(a));
        uint16_t cream=canvas.color565(242,224,255);
        canvas.fillCircle(x,y-2,6,cream);canvas.fillRect(x-6,y-2,13,9,cream);
        for(int k=-4;k<=4;k+=4)canvas.fillTriangle(x+k-2,y+6,x+k+2,y+6,x+k,y+9,cream);
        canvas.fillCircle(x-2,y-1,1,TFT_BLACK);canvas.fillCircle(x+3,y-1,1,TFT_BLACK);
    }
}

static void drawFrame(uint32_t now) {
    uint32_t startUs = micros();
    if (petted && (uint32_t)(now - petSince) >= (halloween ? 5000u : 4000u)) petted = false;
    activeClip = play.casting ? 9 : petted ? (halloween ? 7 : 5) : mood;
    uint32_t clipTime = now - (petted ? petSince : modeSince);
    int clipFrames=halloween ? halloweenAssets.frames : CLIP_FRAMES;
    int frame = activeClip * clipFrames + (clipTime / FRAME_MS) % clipFrames;
    canvas.fillScreen(TFT_BLACK);
    uint32_t size;
    const uint8_t* jpeg;
    if(halloween)jpeg=halloweenAssets.frame(frame,size);
    else if(companion.active()) {
        int cf=companion.frame(now); uint32_t offset=companion_offsets[cf];
        jpeg=companion_jpeg+offset; size=companion_offsets[cf+1]-offset;
    }
    else { uint32_t offset=avatar_offsets[frame]; jpeg=avatar_jpeg+offset;size=avatar_offsets[frame+1]-offset; }
    if (!jpeg || !canvas.drawJpg(jpeg, size, ORIGIN, ORIGIN)) {
        ++decodeErrors;
    }
    if (petted && halloween)drawBats(clipTime,frame);
    if(halloween)drawMagic(now);
    if(dreaming())drawDreams(now-modeSince);
    if (!halloween && companion.gesture==Companion::Hug) {
        clipTime=now-companion.gestureAt;
        for (int i = 0; i < 3; ++i) {
            int x = 55 + i * 65;
            int y = 65 - ((clipTime / 60 + i * 12) % 35);
            uint16_t pink = canvas.color565(245, 110, 165);
            canvas.fillCircle(x - 2, y, 3, pink);
            canvas.fillCircle(x + 2, y, 3, pink);
            canvas.fillTriangle(x - 5, y + 1, x + 5, y + 1, x, y + 7, pink);
        }
    }
    uint32_t accent = halloween ? 0xff9134 : ACCENTS[mood];
    uint16_t color = canvas.color565((accent >> 16) & 255, (accent >> 8) & 255, accent & 255);
    canvas.drawCircle(119, 119, 113, canvas.color565(28, 22, 42));
    canvas.setTextDatum(middle_center);
    canvas.setTextSize(1);
    canvas.setFont(&fonts::Font0);
    canvas.setTextColor(color, TFT_BLACK);
    canvas.drawString(halloween ? "MUSE HALLOWEEN" : "M U S E", 120, 16);
    for (int i = 0; i < moodCount(); ++i) {
        canvas.fillCircle(120-(moodCount()-1)*5 + i * 10, 222, i == mood ? 3 : 1,
                          i == mood ? color : canvas.color565(50, 45, 65));
    }
    if ((int32_t)(hintUntil - now) > 0) {
        canvas.fillRect(55, 203, 130, 10, TFT_BLACK);
        canvas.drawString(automatic ? "AUTO" : moodLabel(mood), 120, 208);
    }
    if(halloween && (play.charge || play.casting || play.tickled)) {
        canvas.fillRect(30,202,180,13,TFT_BLACK);
        canvas.drawString(play.casting ? "ABRACADABRA!" : play.tickled ? "JI JI JI!" : play.charge==8 ? "PULSA PARA LANZAR" : "GIRA PARA CARGAR",120,208);
        if(play.charge)for(int i=0;i<8;i++)canvas.fillRect(82+i*10,194,7,3,i<play.charge ? color : canvas.color565(45,30,50));
    }
    if(!halloween && companion.active()) {
        canvas.fillRect(30,202,180,13,TFT_BLACK);
        canvas.drawString(companion.label(),120,208);
    }
    canvas.pushSprite(0, 0);
    ++frameCount;
    uint32_t elapsed = micros() - startUs;
    if (elapsed > maxFrameUs) maxFrameUs = elapsed;
}

// Capture the actual framebuffer generated by this device, for USB validation.
static void snapshot() {
    if (!displayReady) { Serial.println("ERROR display"); return; }
    Serial.println("FRAME 240 240 RGB565LE 115200");
    lgfx::rgb565_t row[SCREEN];
    for (int y = 0; y < SCREEN; ++y) {
        canvas.readRect(0, y, SCREEN, 1, row);
        Serial.write(reinterpret_cast<const uint8_t*>(row), sizeof(row));
        delay(1);
    }
    Serial.println("\nFRAME_END");
}

static void handleCommand() {
    command[commandLen] = 0;
    int value, x, y;
    if (!strcmp(command, "status")) status();
    else if (!strcmp(command, "snapshot")) snapshot();
    else if (!strcmp(command, "selftest companion")) { Serial.println(testCompanion() ? "OK selftest companion" : "ERROR selftest companion"); }
    else if (!strcmp(command, "selftest life")) { Serial.println(testLife() ? "OK selftest life" : "ERROR selftest life"); }
    else if (sscanf(command,"touch %d %d",&x,&y)==2 && x>=0 && x<240 && y>=0 && y<240) {
        touchDown(x,y); Serial.println("OK touch");
    }
    else if (!strcmp(command,"release")) { touchUp(); Serial.println("OK release"); }
    else if (!strcmp(command, "pet")) { pet(); Serial.println("OK pet"); }
    else if (!strcmp(command, "click")) { if(sleeping)setSleeping(false);else clickButton(); Serial.println("OK click"); }
    else if (!strcmp(command, "selftest play")) { Serial.println(testPlayEffects() ? "OK selftest play" : "ERROR selftest play"); }
    else if (sscanf(command,"turn %d",&value)==1 && value!=0 && value>=-100 && value<=100) { turnWheel(value);Serial.println("OK turn"); }
    else if (!strcmp(command, "sleep")) { setSleeping(true); Serial.println("OK sleep"); }
    else if (!strcmp(command, "wake")) { setSleeping(false); Serial.println("OK wake"); }
    else if (!strcmp(command, "theme normal")) { setTheme(false); Serial.println("OK theme normal"); }
    else if (!strcmp(command, "theme halloween")) { Serial.println(setTheme(true) ? "OK theme halloween" : "ERROR halloween assets"); }
    else if (!strcmp(command, "selftest input")) { Serial.println(testButtonActions() ? "OK selftest input" : "ERROR selftest input"); }
    else if (!strcmp(command, "selftest assets")) {
        uint8_t invalid[48]={0};
        bool passed=HalloweenAssets::validate(invalid,48)!=nullptr;
        if(halloweenAssets.data)passed=passed && HalloweenAssets::validate(halloweenAssets.data,48)!=nullptr;
        Serial.println(passed ? "OK selftest assets" : "ERROR selftest assets");
    }
    else if (!strcmp(command, "auto on")) { startAutomatic(); Serial.println("OK auto on"); }
    else if (!strcmp(command, "auto off")) { automatic = false; temporarySelection=false; life.manual(millis()); showHint(); Serial.println("OK auto off"); }
    else if (sscanf(command, "mode %d", &value) == 1 && value >= 0 && value < moodCount()) {
        selectMood(value); Serial.println("OK mode");
    } else if (sscanf(command, "brightness %d", &value) == 1 && value >= 20 && value <= 255) {
        brightness = value;
        interact();
        if (!sleeping) M5Dial.Display.setBrightness(brightness);
        Serial.println("OK brightness");
    } else Serial.println("ERROR command");
}

void setup() {
    auto cfg = M5.config();
    cfg.serial_baudrate = 115200;
    cfg.internal_mic = false;
    cfg.internal_spk = false;
    cfg.internal_imu = false;
    cfg.internal_rtc = false;
    cfg.external_display_value = 0;
    cfg.output_power = false;
    cfg.fallback_board = m5::board_t::board_M5Dial;
    M5Dial.begin(cfg, true, false);  // Encoder on; RFID off.
    M5Dial.Display.setRotation(0);
    M5Dial.Display.setBrightness(brightness);
    M5Dial.BtnA.setHoldThresh(1000);
    encoderBase = M5Dial.Encoder.read();
    canvas.setColorDepth(16);
    canvas.setPsram(false);
    displayReady = M5Dial.Display.getBoard() == m5::board_t::board_M5Dial
                   && M5Dial.Display.width() == SCREEN && M5Dial.Display.height() == SCREEN
                   && canvas.createSprite(SCREEN, SCREEN) != nullptr;
    if (!displayReady) {
        M5Dial.Display.fillScreen(TFT_BLACK);
        M5Dial.Display.setTextColor(TFT_RED);
        M5Dial.Display.drawString("ERROR: MEMORIA", 45, 110);
    }
    halloweenAssets.begin();
    modeSince = millis();
    startAutomatic();
    Serial.printf("MuseDial ready; reset_reason=%d\n", (int)esp_reset_reason());
    status();
}

void loop() {
    M5Dial.update();
    uint32_t now = millis();
    if(M5Dial.BtnA.wasPressed()) {
        ++buttonCount;
        if(!life.asleep())interact();
    }
    // Touch can precede the mechanical click on the same screen press.
    if(wakeProtection && uint32_t(now-lastWakeAt)>=300)wakeProtection=false;
    switch(buttonActions.update(M5Dial.BtnA.isPressed(),now,sleeping || wakeProtection || life.asleep())) {
        case ButtonAction::Wake: if(sleeping)setSleeping(false);else wakeCharacter(); break;
        case ButtonAction::Theme: if(!setTheme(!halloween))showHint(); break;
        case ButtonAction::Sleep: setSleeping(!sleeping); break;
        case ButtonAction::Click: clickButton(); break;
        default: break;
    }
    auto touch = M5Dial.Touch.getDetail();
    if(!M5Dial.BtnA.isPressed()) {
        if(touch.wasPressed()) { ++touchCount; touchDown(touch.x,touch.y); }
        if(touch.isPressed() && life.touching) {
            life.lastInteraction=now;
            if(!life.consumeTouch && !halloween)companion.move(touch.x,touch.y);
        }
    } else if(companion.touching)companion.clear();
    if(touch.wasReleased())touchUp();
    long position = M5Dial.Encoder.read();
    long delta = position - encoderBase;
    if (delta >= 4 || delta <= -4) {
        long steps = delta / 4;  // Vendor: 64 edges / 16 detents.
        encoderBase += steps * 4;
        encoderCount += (uint32_t)labs(steps);
        if (sleeping) setSleeping(false);
        turnWheel((int)steps);
    }
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
            if (commandOverflow) Serial.println("ERROR command too long");
            else if (commandLen) handleCommand();
            commandLen = 0; commandOverflow = false;
        } else if (c != '\r') {
            if (commandLen < sizeof(command) - 1) command[commandLen++] = c;
            else commandOverflow = true;
        }
    }
    now = millis();  // Commands/snapshots may advance time or reset modeSince.
    play.update(now);
    companion.update(now);
    if(petted && uint32_t(now-petSince)>=(halloween ? 5000u : 4000u))petted=false;
    bool busy=petted || companion.active() || play.casting || M5Dial.BtnA.isPressed();
    if(temporarySelection && !sleeping && !busy && uint32_t(now-selectionSince)>=10000)startAutomatic();
    if(automatic && !sleeping) {
        int next=life.tick(now,busy,esp_random());
        if(next>=0) { mood=next; modeSince=now; }
    }
    if (displayReady && !sleeping && now - lastFrame >= FRAME_MS) {
        lastFrame = now;
        drawFrame(millis());
    }
    if (Serial && now - lastStatus >= 15000) { lastStatus = now; status(); }
    delay(2);
}
