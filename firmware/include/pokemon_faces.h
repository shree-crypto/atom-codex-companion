#pragma once
#include <M5Unified.h>
#include <cmath>
#include "protocol.h"
static constexpr uint8_t FaceThemeCount=9;
static const char* const FaceThemeNames[]={"robot","pikachu","charmander","squirtle","bulbasaur","eevee","psyduck","jigglypuff","snorlax"};
inline void drawPokemonFace(lgfx::LGFXBase& d,uint8_t theme,State state,uint32_t age,bool muted){
    static const uint32_t backgrounds[]={0,0xffda32,0xfa8c28,0x83bdcf,0x82c6a6,0xad743e,0xf7cc39,0xf5bed6,0x217b7d};
    static const uint32_t irises[]={0,0x272526,0x237e9c,0xa43965,0xac3453,0x593e31,0x171f25,0x258aa8,0x3c3432};
    auto colour=[&](uint32_t rgb){return d.color565((rgb>>16)&255,(rgb>>8)&255,rgb&255);};
    const auto bg=colour(backgrounds[theme]),iris=colour(irises[theme]),ink=colour(0x343031),white=colour(0xfffbed);
    const bool pikachu=theme==1,dragon=theme==2,bulb=theme==4,duck=theme==6,snorlax=theme==8;
    const float phase=age*.001f;
    const int bob=int(.8f*std::sin(phase*1.5f));
    const int gaze=state==State::Working?int(3.2f*std::sin(phase*1.8f)):int(std::sin(phase*.65f));
    float blink=1;const auto b=age%4300;
    if(b>=4000&&state!=State::NeedsInput)blink=std::max(.06f,std::abs(float(b)-4150)/150.f);
    if(state==State::Interrupted)blink=.28f;
    d.startWrite();d.fillScreen(bg);
    if(snorlax){d.fillRoundRect(0,36,128,100,18,colour(0xf5e5bc));}
    if(theme==5){for(int x=0;x<128;x+=21)d.fillTriangle(x,106+bob,x+21,106+bob,x+10,122+bob,colour(0xf2daa9));d.fillRect(0,118,128,10,colour(0xf2daa9));}
    if(pikachu){d.fillCircle(20,79+bob,9,colour(0xed4c49));d.fillCircle(108,79+bob,9,colour(0xed4c49));}
    if(bulb){auto c=colour(0x388d76);d.fillTriangle(57,14,72,16,65,30,c);d.fillTriangle(44,27,53,30,48,38,c);d.fillTriangle(78,28,85,35,73,36,c);}
    if(theme==7){d.drawCircle(65,14,8,colour(0xd68db7));d.drawCircle(65,14,7,colour(0xd68db7));d.fillCircle(68,12,4,bg);}
    for(int i=0;i<2;++i){
        const int x=39+i*50,y=61+bob;
        if(state==State::Finished||snorlax){
            for(int dx=-11;dx<=11;++dx)d.fillCircle(x+dx,y-4+(dx*dx)/24,1,ink);
        }else{
            const int rx=duck?14:pikachu?8:12;
            const int ry=std::max(2,int((duck?15:pikachu?10:18)*blink*(state==State::NeedsInput?1.14f:1.f)));
            d.fillEllipse(x,y,rx,ry,white);
            if(duck)d.fillCircle(x+gaze,y,2,ink);
            else{
                d.fillEllipse(x+gaze,y+int(3*blink),pikachu?7:9,std::max(1,int((pikachu?8:14)*blink)),iris);
                d.fillEllipse(x+gaze,y,pikachu?6:7,std::max(1,int((pikachu?8:11)*blink)),ink);
                d.fillEllipse(x+gaze-3,y-int(8*blink),3,std::max(1,int(5*blink)),white);
                if(blink>.6f)d.fillCircle(x+gaze+4,y+7,1,white);
            }
        }
    }
    if(state==State::Error){d.drawLine(26,36+bob,48,43+bob,ink);d.drawLine(80,43+bob,102,36+bob,ink);}
    if(duck){d.fillEllipse(64,88+bob,31,14,colour(0xf6e4a0));d.drawEllipse(64,88+bob,31,14,ink);d.fillCircle(59,80+bob,1,ink);d.fillCircle(69,80+bob,1,ink);}
    else if(dragon||bulb||theme==3){d.drawPixel(60,78+bob,ink);d.drawPixel(68,78+bob,ink);}
    else d.fillTriangle(61,77+bob,67,77+bob,64,80+bob,ink);
    const bool open=state==State::Finished||state==State::NeedsInput;
    if(open&&!duck){
        d.fillEllipse(64,98+bob,20,13,colour(0x79334f));d.fillEllipse(64,105+bob,11,5,colour(0xee8c9c));
        if(dragon||bulb||snorlax){d.fillTriangle(44,90+bob,50,90+bob,47,96+bob,white);d.fillTriangle(78,90+bob,84,90+bob,81,96+bob,white);}
    }else if(state==State::Disconnected)d.drawLine(54,94+bob,74,94+bob,ink);
    else for(int dx=-20;dx<=20;++dx){int y=92+int((state==State::Error?-5:7)*(1-dx*dx/400.f));d.fillCircle(64+dx,y+bob,1,ink);}
    d.setTextSize(2);d.setTextColor(ink,bg);
    if(state==State::NeedsInput)d.drawString("?",106,8+int(1.5f*std::sin(phase*3)));
    if(state==State::Working)for(int i=0;i<3;++i)d.fillCircle(54+i*10,115,2+int(std::sin(phase*3-i)),ink);
    if(state==State::Interrupted){d.setTextSize(1);d.drawString("zZ",102,15);}
    d.setTextSize(1);if(muted)d.drawString("M",116,116);
    d.endWrite();
}
