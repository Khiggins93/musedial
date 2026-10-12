#pragma once
#include <esp_partition.h>
#include <stdint.h>
#include <string.h>
struct HalloweenAssets {
  const uint8_t* data=nullptr;
  esp_partition_mmap_handle_t mapping=0;
  uint32_t count=0, frames=0, jpeg=0, spans=0;
  const char* error="not_loaded";
  static uint32_t word(const uint8_t* p) { uint32_t n; memcpy(&n,p,4); return n; }
  static uint32_t crc(const uint8_t* p,uint32_t n) {
    uint32_t c=~0u;
    while(n--) { c^=*p++; for(int i=0;i<8;++i)c=(c>>1)^(0xEDB88320u & (0u-(c&1))); }
    return ~c;
  }
  static const char* validate(const uint8_t* p,uint32_t size) {
    if(size<48 || memcmp(p,"HWEEN3\0\0",8)) return "magic";
    auto w=[p](int i){return word(p+8+i*4);};
    if(w(0)!=1 || w(1)!=12 || (w(2)!=40 && w(2)!=32) || w(3)!=192 || w(4)!=192 || w(5)!=20) return "format";
    uint32_t n=w(1)*w(2), total=w(6), j=w(7), s=w(8);
    if(total>size || total>3*1024*1024 || s!=48+4*(n+1) || j!=s+n*384 || total<=j) return "bounds";
    if(crc(p+48,total-48)!=w(9))return "crc";
    if(word(p+48)!=0 || word(p+48+4*n)!=total-j)return "offsets";
    for(uint32_t i=0;i<n;i++) {
      uint32_t a=word(p+48+4*i),b=word(p+52+4*i);
      if(b<=a+2 || b>total-j || p[j+a]!=0xff || p[j+a+1]!=0xd8)return "jpeg";
    }
    for(uint32_t i=s;i<j;i+=2)if(!((p[i]==255 && p[i+1]==0)||(p[i]<=p[i+1] && p[i+1]<192)))return "silhouette";
    return nullptr;
  }
  bool begin() {
    const auto* part=esp_partition_find_first(ESP_PARTITION_TYPE_DATA,(esp_partition_subtype_t)0x40,"halloween");
    if(!part){error="partition_missing";return false;}
    const void* mapped=nullptr;
    if(esp_partition_mmap(part,0,part->size,ESP_PARTITION_MMAP_DATA,&mapped,&mapping)!=ESP_OK){error="mmap";return false;}
    auto p=(const uint8_t*)mapped;
    error=validate(p,part->size);
    if(error){esp_partition_munmap(mapping);return false;}
    data=p; frames=word(p+16); count=frames*12; jpeg=word(p+36); spans=word(p+40); return true;
  }
  const uint8_t* frame(uint32_t i,uint32_t& size)const {
    if(!data || i>=count){size=0;return nullptr;}
    uint32_t a=word(data+48+4*i),b=word(data+52+4*i);size=b-a;return data+jpeg+a;
  }
  bool covers(uint32_t frame,int x,int y)const {
    if(!data || frame>=count || x<0 || y<0 || x>=192 || y>=192)return false;
    auto p=data+spans+frame*384+y*2;return x>=p[0] && x<=p[1];
  }
};
