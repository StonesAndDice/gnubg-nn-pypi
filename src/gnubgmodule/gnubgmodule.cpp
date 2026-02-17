/*
 * gnubgmodule.cc
 *
 * Originally by Joseph Heled <joseph@gnubg.org>, 2000
 * Adapted for Python 3 and Meson build system by David Reay
 * <dr323090@falmouth.ac.uk>
 *
 * Copyright 2000 Joseph Heled
 * Copyright 2025 David Reay
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of version 2 of the GNU General Public License as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <Python.h>

// Windows doesn’t have strcasecmp or strdup or setenv:
#if defined(_WIN32)
#include <stdlib.h>  // for _putenv_s
#define strcasecmp _stricmp
#define strdup _strdup
#endif

#if defined(_WIN32)
// Windows: use Win32 loader APIs
#include <windows.h>

#elif defined(__unix__) || defined(__APPLE__)
// Unix/macOS: use dladdr() + dirname()
#include <dlfcn.h>
#include <libgen.h>

#endif

#include <algorithm>
#include <cstdarg>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "analyze.h"
#include "bm.h"
#include "equities.h"
#include "gnubgmodule.h"
#include "misc.h"
#include "player.h"
#include "stdutil.h"

extern "C" {
#include "eval.h"
#include "inputs.h"
#include "positionid.h"

typedef struct NetDef NetDef;
extern NetDef *nets
    [];  // pulls in the real definition from eval.c
         // :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
void initnet(
    void);  // this will populate nets[]
            // :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}
}

#include "br.h"
#include "osr.h"

extern "C" PyMODINIT_FUNC PyInit__gnubg_nn(void);

// shorthand 26‐element board for bearoff/resign logic
typedef int16_t AnalyzeBoard[26];

// The global “analyzer” used for the resign call
namespace {
Player analyzer;
}

//-----------------------------------------------------------------------------
// Which “ply” to evaluate.  Must match your enum below.
enum {
  PLY_OSR = -2,
  PLY_BEAROFF = -3,
  PLY_PRUNE = -4,
  PLY_1SBEAR = -5,
  PLY_RACENET = -6,
  PLY_1ANDHALF = -7,
  PLY_1SRACE = -8,
};

unsigned int const nData = 400;

static float ocrData[nData][2] = {
    {/*1 , */ 1.0000f, 0.0000f},    {/*2 , */ 1.0000f, 0.0000f},
    {/*3 , */ 1.0000f, 0.0000f},    {/*4 , */ 1.0556f, 0.2291f},
    {/*5 , */ 1.1389f, 0.3458f},    {/*6 , */ 1.2500f, 0.4330f},
    {/*7 , */ 1.3642f, 0.4876f},    {/*8 , */ 1.5401f, 0.5226f},
    {/*9 , */ 1.6983f, 0.5234f},    {/*10 , */ 1.8404f, 0.5097f},
    {/*11 , */ 1.9462f, 0.5277f},   {/*12 , */ 2.0718f, 0.5433f},
    {/*13 , */ 2.1892f, 0.5794f},   {/*14 , */ 2.2908f, 0.6378f},
    {/*15 , */ 2.4052f, 0.6880f},   {/*16 , */ 2.5256f, 0.7294f},
    {/*17 , */ 2.6745f, 0.7213f},   {/*18 , */ 2.7905f, 0.7534f},
    {/*19 , */ 2.9042f, 0.7878f},   {/*20 , */ 3.0184f, 0.8244f},
    {/*21 , */ 3.1588f, 0.8089f},   {/*22 , */ 3.2708f, 0.8484f},
    {/*23 , */ 3.3829f, 0.8884f},   {/*24 , */ 3.5021f, 0.9203f},
    {/*25 , */ 3.6485f, 0.8860f},   {/*26 , */ 3.7668f, 0.9129f},
    {/*27 , */ 3.8828f, 0.9424f},   {/*28 , */ 4.0056f, 0.9610f},
    {/*29 , */ 4.1278f, 0.9795f},   {/*30 , */ 4.2492f, 0.9983f},
    {/*31 , */ 4.3696f, 1.0191f},   {/*32 , */ 4.4950f, 1.0303f},
    {/*33 , */ 4.6199f, 1.0417f},   {/*34 , */ 4.7419f, 1.0577f},
    {/*35 , */ 4.8628f, 1.0764f},   {/*36 , */ 4.9854f, 1.0918f},
    {/*37 , */ 5.1091f, 1.1044f},   {/*38 , */ 5.2300f, 1.1231f},
    {/*39 , */ 5.3517f, 1.1401f},   {/*40 , */ 5.4742f, 1.1555f},
    {/*41 , */ 5.5988f, 1.1647f},   {/*42 , */ 5.7207f, 1.1805f},
    {/*43 , */ 5.8423f, 1.1966f},   {/*44 , */ 5.9646f, 1.2114f},
    {/*45 , */ 6.0881f, 1.2221f},   {/*46 , */ 6.2100f, 1.2374f},
    {/*47 , */ 6.3318f, 1.2528f},   {/*48 , */ 6.4544f, 1.2662f},
    {/*49 , */ 6.5777f, 1.2772f},   {/*50 , */ 6.6999f, 1.2909f},
    {/*51 , */ 6.8220f, 1.3050f},   {/*52 , */ 6.9446f, 1.3175f},
    {/*53 , */ 7.0672f, 1.3300f},   {/*54 , */ 7.1895f, 1.3430f},
    {/*55 , */ 7.3118f, 1.3561f},   {/*56 , */ 7.4344f, 1.3682f},
    {/*57 , */ 7.5570f, 1.3799f},   {/*58 , */ 7.6793f, 1.3924f},
    {/*59 , */ 7.8017f, 1.4048f},   {/*60 , */ 7.9242f, 1.4168f},
    {/*61 , */ 8.0467f, 1.4283f},   {/*62 , */ 8.1691f, 1.4404f},
    {/*63 , */ 8.2915f, 1.4524f},   {/*64 , */ 8.4139f, 1.4640f},
    {/*65 , */ 8.5365f, 1.4751f},   {/*66 , */ 8.6589f, 1.4867f},
    {/*67 , */ 8.7813f, 1.4982f},   {/*68 , */ 8.9038f, 1.5095f},
    {/*69 , */ 9.0263f, 1.5205f},   {/*70 , */ 9.1487f, 1.5317f},
    {/*71 , */ 9.2711f, 1.5429f},   {/*72 , */ 9.3936f, 1.5538f},
    {/*73 , */ 9.5161f, 1.5645f},   {/*74 , */ 9.6385f, 1.5754f},
    {/*75 , */ 9.7609f, 1.5862f},   {/*76 , */ 9.8834f, 1.5968f},
    {/*77 , */ 10.0058f, 1.6073f},  {/*78 , */ 10.1283f, 1.6179f},
    {/*79 , */ 10.2507f, 1.6284f},  {/*80 , */ 10.3732f, 1.6387f},
    {/*81 , */ 10.4956f, 1.6490f},  {/*82 , */ 10.6181f, 1.6593f},
    {/*83 , */ 10.7405f, 1.6695f},  {/*84 , */ 10.8630f, 1.6796f},
    {/*85 , */ 10.9854f, 1.6896f},  {/*86 , */ 11.1079f, 1.6997f},
    {/*87 , */ 11.2303f, 1.7096f},  {/*88 , */ 11.3528f, 1.7195f},
    {/*89 , */ 11.4752f, 1.7293f},  {/*90 , */ 11.5977f, 1.7391f},
    {/*91 , */ 11.7201f, 1.7488f},  {/*92 , */ 11.8426f, 1.7585f},
    {/*93 , */ 11.9650f, 1.7681f},  {/*94 , */ 12.0875f, 1.7777f},
    {/*95 , */ 12.2099f, 1.7872f},  {/*96 , */ 12.3324f, 1.7967f},
    {/*97 , */ 12.4548f, 1.8061f},  {/*98 , */ 12.5773f, 1.8154f},
    {/*99 , */ 12.6997f, 1.8247f},  {/*100 , */ 12.8222f, 1.8340f},
    {/*101 , */ 12.9446f, 1.8432f}, {/*102 , */ 13.0671f, 1.8524f},
    {/*103 , */ 13.1895f, 1.8616f}, {/*104 , */ 13.3120f, 1.8706f},
    {/*105 , */ 13.4344f, 1.8797f}, {/*106 , */ 13.5569f, 1.8887f},
    {/*107 , */ 13.6793f, 1.8976f}, {/*108 , */ 13.8018f, 1.9065f},
    {/*109 , */ 13.9242f, 1.9154f}, {/*110 , */ 14.0466f, 1.9242f},
    {/*111 , */ 14.1691f, 1.9331f}, {/*112 , */ 14.2915f, 1.9418f},
    {/*113 , */ 14.4140f, 1.9505f}, {/*114 , */ 14.5364f, 1.9592f},
    {/*115 , */ 14.6589f, 1.9678f}, {/*116 , */ 14.7813f, 1.9764f},
    {/*117 , */ 14.9038f, 1.9850f}, {/*118 , */ 15.0262f, 1.9935f},
    {/*119 , */ 15.1487f, 2.0020f}, {/*120 , */ 15.2711f, 2.0104f},
    {/*121 , */ 15.3936f, 2.0189f}, {/*122 , */ 15.5160f, 2.0272f},
    {/*123 , */ 15.6385f, 2.0356f}, {/*124 , */ 15.7609f, 2.0439f},
    {/*125 , */ 15.8834f, 2.0522f}, {/*126 , */ 16.0058f, 2.0604f},
    {/*127 , */ 16.1283f, 2.0686f}, {/*128 , */ 16.2507f, 2.0768f},
    {/*129 , */ 16.3732f, 2.0850f}, {/*130 , */ 16.4956f, 2.0931f},
    {/*131 , */ 16.6181f, 2.1012f}, {/*132 , */ 16.7405f, 2.1092f},
    {/*133 , */ 16.8630f, 2.1173f}, {/*134 , */ 16.9854f, 2.1253f},
    {/*135 , */ 17.1079f, 2.1332f}, {/*136 , */ 17.2303f, 2.1411f},
    {/*137 , */ 17.3528f, 2.1490f}, {/*138 , */ 17.4752f, 2.1569f},
    {/*139 , */ 17.5977f, 2.1648f}, {/*140 , */ 17.7201f, 2.1726f},
    {/*141 , */ 17.8426f, 2.1804f}, {/*142 , */ 17.9650f, 2.1881f},
    {/*143 , */ 18.0875f, 2.1959f}, {/*144 , */ 18.2099f, 2.2036f},
    {/*145 , */ 18.3324f, 2.2113f}, {/*146 , */ 18.4548f, 2.2189f},
    {/*147 , */ 18.5773f, 2.2265f}, {/*148 , */ 18.6997f, 2.2341f},
    {/*149 , */ 18.8222f, 2.2417f}, {/*150 , */ 18.9446f, 2.2493f},
    {/*151 , */ 19.0671f, 2.2568f}, {/*152 , */ 19.1895f, 2.2643f},
    {/*153 , */ 19.3120f, 2.2718f}, {/*154 , */ 19.4344f, 2.2793f},
    {/*155 , */ 19.5569f, 2.2867f}, {/*156 , */ 19.6793f, 2.2941f},
    {/*157 , */ 19.8018f, 2.3015f}, {/*158 , */ 19.9242f, 2.3088f},
    {/*159 , */ 20.0466f, 2.3161f}, {/*160 , */ 20.1691f, 2.3235f},
    {/*161 , */ 20.2915f, 2.3307f}, {/*162 , */ 20.4140f, 2.3380f},
    {/*163 , */ 20.5364f, 2.3452f}, {/*164 , */ 20.6589f, 2.3525f},
    {/*165 , */ 20.7813f, 2.3597f}, {/*166 , */ 20.9038f, 2.3669f},
    {/*167 , */ 21.0262f, 2.3740f}, {/*168 , */ 21.1487f, 2.3811f},
    {/*169 , */ 21.2711f, 2.3883f}, {/*170 , */ 21.3936f, 2.3953f},
    {/*171 , */ 21.5160f, 2.4024f}, {/*172 , */ 21.6385f, 2.4095f},
    {/*173 , */ 21.7609f, 2.4165f}, {/*174 , */ 21.8834f, 2.4235f},
    {/*175 , */ 22.0058f, 2.4305f}, {/*176 , */ 22.1283f, 2.4375f},
    {/*177 , */ 22.2507f, 2.4444f}, {/*178 , */ 22.3732f, 2.4513f},
    {/*179 , */ 22.4956f, 2.4582f}, {/*180 , */ 22.6181f, 2.4651f},
    {/*181 , */ 22.7405f, 2.4720f}, {/*182 , */ 22.8630f, 2.4788f},
    {/*183 , */ 22.9854f, 2.4857f}, {/*184 , */ 23.1079f, 2.4925f},
    {/*185 , */ 23.2303f, 2.4993f}, {/*186 , */ 23.3528f, 2.5061f},
    {/*187 , */ 23.4752f, 2.5128f}, {/*188 , */ 23.5977f, 2.5196f},
    {/*189 , */ 23.7201f, 2.5263f}, {/*190 , */ 23.8426f, 2.5330f},
    {/*191 , */ 23.9650f, 2.5397f}, {/*192 , */ 24.0875f, 2.5463f},
    {/*193 , */ 24.2099f, 2.5530f}, {/*194 , */ 24.3324f, 2.5597f},
    {/*195 , */ 24.4548f, 2.5662f}, {/*196 , */ 24.5773f, 2.5728f},
    {/*197 , */ 24.6997f, 2.5794f}, {/*198 , */ 24.8222f, 2.5860f},
    {/*199 , */ 24.9446f, 2.5925f}, {/*200 , */ 25.0671f, 2.5991f},
    {/*201 , */ 25.1895f, 2.6056f}, {/*202 , */ 25.3120f, 2.6121f},
    {/*203 , */ 25.4344f, 2.6186f}, {/*204 , */ 25.5569f, 2.6251f},
    {/*205 , */ 25.6793f, 2.6315f}, {/*206 , */ 25.8018f, 2.6379f},
    {/*207 , */ 25.9242f, 2.6443f}, {/*208 , */ 26.0466f, 2.6508f},
    {/*209 , */ 26.1691f, 2.6572f}, {/*210 , */ 26.2915f, 2.6635f},
    {/*211 , */ 26.4140f, 2.6699f}, {/*212 , */ 26.5364f, 2.6762f},
    {/*213 , */ 26.6589f, 2.6826f}, {/*214 , */ 26.7813f, 2.6889f},
    {/*215 , */ 26.9038f, 2.6952f}, {/*216 , */ 27.0262f, 2.7015f},
    {/*217 , */ 27.1487f, 2.7077f}, {/*218 , */ 27.2711f, 2.7140f},
    {/*219 , */ 27.3936f, 2.7202f}, {/*220 , */ 27.5160f, 2.7264f},
    {/*221 , */ 27.6385f, 2.7327f}, {/*222 , */ 27.7609f, 2.7389f},
    {/*223 , */ 27.8834f, 2.7451f}, {/*224 , */ 28.0058f, 2.7512f},
    {/*225 , */ 28.1283f, 2.7574f}, {/*226 , */ 28.2507f, 2.7635f},
    {/*227 , */ 28.3732f, 2.7697f}, {/*228 , */ 28.4956f, 2.7757f},
    {/*229 , */ 28.6181f, 2.7819f}, {/*230 , */ 28.7405f, 2.7880f},
    {/*231 , */ 28.8630f, 2.7940f}, {/*232 , */ 28.9854f, 2.8001f},
    {/*233 , */ 29.1079f, 2.8061f}, {/*234 , */ 29.2303f, 2.8122f},
    {/*235 , */ 29.3528f, 2.8183f}, {/*236 , */ 29.4752f, 2.8242f},
    {/*237 , */ 29.5977f, 2.8302f}, {/*238 , */ 29.7201f, 2.8362f},
    {/*239 , */ 29.8426f, 2.8422f}, {/*240 , */ 29.9650f, 2.8481f},
    {/*241 , */ 30.0875f, 2.8541f}, {/*242 , */ 30.2099f, 2.8600f},
    {/*243 , */ 30.3324f, 2.8659f}, {/*244 , */ 30.4548f, 2.8718f},
    {/*245 , */ 30.5773f, 2.8778f}, {/*246 , */ 30.6997f, 2.8836f},
    {/*247 , */ 30.8222f, 2.8895f}, {/*248 , */ 30.9446f, 2.8954f},
    {/*249 , */ 31.0671f, 2.9012f}, {/*250 , */ 31.1895f, 2.9071f},
    {/*251 , */ 31.3120f, 2.9129f}, {/*252 , */ 31.4344f, 2.9187f},
    {/*253 , */ 31.5569f, 2.9245f}, {/*254 , */ 31.6793f, 2.9303f},
    {/*255 , */ 31.8017f, 2.9361f}, {/*256 , */ 31.9242f, 2.9418f},
    {/*257 , */ 32.0466f, 2.9476f}, {/*258 , */ 32.1691f, 2.9533f},
    {/*259 , */ 32.2915f, 2.9591f}, {/*260 , */ 32.4140f, 2.9649f},
    {/*261 , */ 32.5364f, 2.9706f}, {/*262 , */ 32.6589f, 2.9763f},
    {/*263 , */ 32.7813f, 2.9820f}, {/*264 , */ 32.9038f, 2.9876f},
    {/*265 , */ 33.0262f, 2.9933f}, {/*266 , */ 33.1487f, 2.9990f},
    {/*267 , */ 33.2711f, 3.0046f}, {/*268 , */ 33.3936f, 3.0102f},
    {/*269 , */ 33.5160f, 3.0159f}, {/*270 , */ 33.6385f, 3.0215f},
    {/*271 , */ 33.7609f, 3.0271f}, {/*272 , */ 33.8834f, 3.0327f},
    {/*273 , */ 34.0058f, 3.0384f}, {/*274 , */ 34.1283f, 3.0439f},
    {/*275 , */ 34.2507f, 3.0494f}, {/*276 , */ 34.3732f, 3.0550f},
    {/*277 , */ 34.4956f, 3.0605f}, {/*278 , */ 34.6181f, 3.0661f},
    {/*279 , */ 34.7405f, 3.0716f}, {/*280 , */ 34.8630f, 3.0772f},
    {/*281 , */ 34.9854f, 3.0826f}, {/*282 , */ 35.1079f, 3.0881f},
    {/*283 , */ 35.2303f, 3.0936f}, {/*284 , */ 35.3528f, 3.0990f},
    {/*285 , */ 35.4752f, 3.1045f}, {/*286 , */ 35.5977f, 3.1099f},
    {/*287 , */ 35.7201f, 3.1154f}, {/*288 , */ 35.8426f, 3.1209f},
    {/*289 , */ 35.9650f, 3.1264f}, {/*290 , */ 36.0875f, 3.1317f},
    {/*291 , */ 36.2099f, 3.1371f}, {/*292 , */ 36.3324f, 3.1426f},
    {/*293 , */ 36.4548f, 3.1479f}, {/*294 , */ 36.5773f, 3.1533f},
    {/*295 , */ 36.6997f, 3.1587f}, {/*296 , */ 36.8222f, 3.1640f},
    {/*297 , */ 36.9446f, 3.1694f}, {/*298 , */ 37.0671f, 3.1748f},
    {/*299 , */ 37.1895f, 3.1801f}, {/*300 , */ 37.3120f, 3.1854f},
    {/*301 , */ 37.4344f, 3.1907f}, {/*302 , */ 37.5568f, 3.1961f},
    {/*303 , */ 37.6793f, 3.2013f}, {/*304 , */ 37.8017f, 3.2066f},
    {/*305 , */ 37.9242f, 3.2119f}, {/*306 , */ 38.0466f, 3.2172f},
    {/*307 , */ 38.1691f, 3.2225f}, {/*308 , */ 38.2915f, 3.2277f},
    {/*309 , */ 38.4140f, 3.2329f}, {/*310 , */ 38.5364f, 3.2382f},
    {/*311 , */ 38.6589f, 3.2435f}, {/*312 , */ 38.7813f, 3.2487f},
    {/*313 , */ 38.9038f, 3.2539f}, {/*314 , */ 39.0262f, 3.2591f},
    {/*315 , */ 39.1487f, 3.2643f}, {/*316 , */ 39.2711f, 3.2695f},
    {/*317 , */ 39.3936f, 3.2747f}, {/*318 , */ 39.5160f, 3.2798f},
    {/*319 , */ 39.6385f, 3.2850f}, {/*320 , */ 39.7609f, 3.2902f},
    {/*321 , */ 39.8834f, 3.2953f}, {/*322 , */ 40.0058f, 3.3006f},
    {/*323 , */ 40.1283f, 3.3056f}, {/*324 , */ 40.2507f, 3.3107f},
    {/*325 , */ 40.3732f, 3.3159f}, {/*326 , */ 40.4956f, 3.3210f},
    {/*327 , */ 40.6181f, 3.3261f}, {/*328 , */ 40.7405f, 3.3312f},
    {/*329 , */ 40.8630f, 3.3362f}, {/*330 , */ 40.9854f, 3.3413f},
    {/*331 , */ 41.1079f, 3.3464f}, {/*332 , */ 41.2303f, 3.3515f},
    {/*333 , */ 41.3528f, 3.3565f}, {/*334 , */ 41.4752f, 3.3616f},
    {/*335 , */ 41.5977f, 3.3666f}, {/*336 , */ 41.7201f, 3.3717f},
    {/*337 , */ 41.8426f, 3.3767f}, {/*338 , */ 41.9650f, 3.3817f},
    {/*339 , */ 42.0875f, 3.3867f}, {/*340 , */ 42.2099f, 3.3917f},
    {/*341 , */ 42.3324f, 3.3967f}, {/*342 , */ 42.4548f, 3.4018f},
    {/*343 , */ 42.5773f, 3.4067f}, {/*344 , */ 42.6997f, 3.4116f},
    {/*345 , */ 42.8222f, 3.4166f}, {/*346 , */ 42.9446f, 3.4216f},
    {/*347 , */ 43.0671f, 3.4265f}, {/*348 , */ 43.1895f, 3.4315f},
    {/*349 , */ 43.3119f, 3.4364f}, {/*350 , */ 43.4344f, 3.4413f},
    {/*351 , */ 43.5568f, 3.4463f}, {/*352 , */ 43.6793f, 3.4512f},
    {/*353 , */ 43.8017f, 3.4561f}, {/*354 , */ 43.9242f, 3.4610f},
    {/*355 , */ 44.0466f, 3.4659f}, {/*356 , */ 44.1691f, 3.4708f},
    {/*357 , */ 44.2915f, 3.4757f}, {/*358 , */ 44.4140f, 3.4805f},
    {/*359 , */ 44.5364f, 3.4855f}, {/*360 , */ 44.6589f, 3.4902f},
    {/*361 , */ 44.7813f, 3.4952f}, {/*362 , */ 44.9038f, 3.5000f},
    {/*363 , */ 45.0262f, 3.5048f}, {/*364 , */ 45.1487f, 3.5097f},
    {/*365 , */ 45.2711f, 3.5145f}, {/*366 , */ 45.3936f, 3.5193f},
    {/*367 , */ 45.5160f, 3.5242f}, {/*368 , */ 45.6385f, 3.5290f},
    {/*369 , */ 45.7609f, 3.5338f}, {/*370 , */ 45.8834f, 3.5385f},
    {/*371 , */ 46.0058f, 3.5434f}, {/*372 , */ 46.1283f, 3.5481f},
    {/*373 , */ 46.2507f, 3.5529f}, {/*374 , */ 46.3732f, 3.5577f},
    {/*375 , */ 46.4956f, 3.5625f}, {/*376 , */ 46.6181f, 3.5672f},
    {/*377 , */ 46.7405f, 3.5719f}, {/*378 , */ 46.8630f, 3.5767f},
    {/*379 , */ 46.9854f, 3.5815f}, {/*380 , */ 47.1079f, 3.5862f},
    {/*381 , */ 47.2303f, 3.5909f}, {/*382 , */ 47.3528f, 3.5956f},
    {/*383 , */ 47.4752f, 3.6004f}, {/*384 , */ 47.5977f, 3.6051f},
    {/*385 , */ 47.7201f, 3.6097f}, {/*386 , */ 47.8426f, 3.6144f},
    {/*387 , */ 47.9650f, 3.6191f}, {/*388 , */ 48.0875f, 3.6238f},
    {/*389 , */ 48.2099f, 3.6284f}, {/*390 , */ 48.3324f, 3.6332f},
    {/*391 , */ 48.4548f, 3.6379f}, {/*392 , */ 48.5773f, 3.6424f},
    {/*393 , */ 48.6997f, 3.6472f}, {/*394 , */ 48.8222f, 3.6518f},
    {/*395 , */ 48.9446f, 3.6564f}, {/*396 , */ 49.0671f, 3.6610f},
    {/*397 , */ 49.1895f, 3.6657f}, {/*398 , */ 49.3119f, 3.6704f},
    {/*399 , */ 49.4344f, 3.6751f}, {/*400 , */ 49.5568f, 3.6996f},
};

float ocr(unsigned int n, float *stdv) {
  if (!(0 < n && n <= nData)) {
    return 0.0f;
  }

  if (stdv) {
    *stdv = ocrData[n - 1][1];
  }

  return ocrData[n - 1][0];
}

// ------------------------------------------------------------------
// Given a 10-byte GNUBG “auch” key, emit the 20-char A–Z position ID
static const char *posString(const unsigned char *auch) {
  static char buf[21];
  for (int i = 0; i < 10; ++i) {
    buf[2 * i] = 'A' + ((auch[i] >> 4) & 0xF);
    buf[2 * i + 1] = 'A' + (auch[i] & 0xF);
  }
  buf[20] = '\0';
  return buf;
}

// Convert a 20‐char A–Z key into the 10‐byte “auch” array:
static unsigned char *auchFromString(const char *str) {
  // str must be length 20
  static unsigned char auch[10];
  for (int i = 0; i < 10; ++i) {
    int hi = str[2 * i] - 'A';
    int lo = str[2 * i + 1] - 'A';
    auch[i] = static_cast<unsigned char>((hi << 4) | lo);
  }
  return auch;
}

// setBoard for resign logic
static void setBoard(AnalyzeBoard out, const int board[2][25]) {
  // bar of + on [0]
  out[0] = board[1][24];
  // points 1..24
  for (int k = 0; k < 24; ++k) {
    int val = 0;
    if (board[1][23 - k] > 0) {
      val = board[1][23 - k];
    } else if (board[0][k] > 0) {
      val = -board[0][k];
    }
    out[k + 1] = val;
  }
  // bar of - at index 25
  out[25] = -board[0][24];
}

// boardString: turn a C board into the “PositionKey” string
static const char *boardString(const int board[2][25]) {
  unsigned char auch[10];
  // PositionKey comes from <eval.h>; it wants Board = int[2][25]
  PositionKey((int(*)[25])board, auch);

  // now convert 10 nybbles to 20-char A…Z string
  static char buf[21];
  for (int i = 0; i < 10; ++i) {
    buf[2 * i] = 'A' + ((auch[i] >> 4) & 0xF);
    buf[2 * i + 1] = 'A' + (auch[i] & 0xF);
  }
  buf[20] = '\0';
  return buf;
}

//-----------------------------------------------------------------------------
// stringToBoard(key, board):
//   key is either a 20-char A–Z string or a 14-char base64 ID;
//   fills int board[2][25] and returns true on success.
static bool stringToBoard(const char *key, int board[2][25]) {
  size_t len = strlen(key);
  if (len == 20) {
    // interpret as PositionKey
    PositionFromKey(board, auchFromString(key));
    return true;
  } else if (len == 14) {
    // interpret as PositionID
    PositionFromID(board, key);
    return true;
  }
  // otherwise invalid
  return false;
}

//-----------------------------------------------------------------------------
// Converter for the “ply” argument: accepts a Python int and checks the range
static int readPly(PyObject *obj, void *out_p) {
  if (!PyLong_Check(obj)) {
    PyErr_SetString(PyExc_TypeError, "ply must be an integer");
    return 0;
  }

  int32_t v = static_cast<int32_t>(PyLong_AsLong(obj));

  // valid if non-negative or one of our special negative codes
  if (v >= 0 || (v <= PLY_OSR && v >= PLY_1ANDHALF)) {
    *static_cast<int *>(out_p) = static_cast<int>(v);
    return 1;
  }

  PyErr_SetString(PyExc_ValueError, "invalid ply");
  return 0;
}

//-----------------------------------------------------------------------------
// Convert a Python object (26-element sequence or string) into
// a 26-entry AnalyzeBoard (short[26]).  Returns 1 on success, 0 on error.
static int anyAnalyzeBoard(PyObject *o, void *out_ptr) {
  // out_ptr really points at an AnalyzeBoard:
  int16_t *board = static_cast<int16_t *>(out_ptr);

  // Case 1: a sequence of length 26
  if (PySequence_Check(o) && PySequence_Size(o) == 26) {
    PyObject *seq = PySequence_Fast(o, "expected 26-element sequence");
    if (!seq)
      return 0;
    int32_t s0 = 0, s1 = 0;
    for (Py_ssize_t k = 0; k < 26; ++k) {
      PyObject *item = PySequence_Fast_GET_ITEM(seq, k);
      if (!PyLong_Check(item)) {
        PyErr_SetString(PyExc_TypeError, "board entries must be ints");
        Py_DECREF(seq);
        return 0;
      }
      int32_t v = static_cast<int32_t>(PyLong_AsLong(item));
      board[k] = static_cast<int16_t>(v);
      if (v > 0)
        s0 += v;
      else if (v < 0)
        s1 += -v;
    }
    Py_DECREF(seq);
    if (!(s0 <= 15 && s1 <= 15)) {
      PyErr_Format(PyExc_ValueError, "Invalid board (x has %ld, o has %ld)", s0,
                   s1);
      return 0;
    }
    return 1;
  }

  // Case 2: a Unicode string key/ID
  if (PyUnicode_Check(o)) {
    const char *s = PyUnicode_AsUTF8(o);
    if (!s)
      return 0;  // error already set

    // First decode into the 2×25 int board:
    int temp[2][25];
    if (!stringToBoard(s, temp)) {
      // stringToBoard should set ValueError if invalid
      return 0;
    }
    // Then convert to AnalyzeBoard layout:
    setBoard(board, temp);
    return 1;
  }

  PyErr_SetString(PyExc_ValueError,
                  "Expected 26-element list or position key string");
  return 0;
}

//-----------------------------------------------------------------------------
// pack_board: turn a C int[2][25] into a Python tuple of two 25-tuples
static PyObject *pack_board(const int board[2][25]) {
  PyObject *outer = PyTuple_New(2);
  if (!outer)
    return NULL;

  for (int s = 0; s < 2; ++s) {
    PyObject *inner = PyTuple_New(25);
    if (!inner) {
      Py_DECREF(outer);
      return NULL;
    }
    for (int p = 0; p < 25; ++p) {
      PyTuple_SET_ITEM(inner, p, PyLong_FromLong(board[s][p]));
    }
    PyTuple_SET_ITEM(outer, s, inner);
  }
  return outer;
}

// anyBoard converter
static int anyBoard(PyObject *obj, void *out_board) {
  // reinterpret the void* as int[2][25]
  int(*board)[25] = reinterpret_cast<int(*)[25]>(out_board);
  if (!PySequence_Check(obj) || PySequence_Size(obj) != 2) {
    PyErr_SetString(PyExc_ValueError,
                    "Expected 2-element sequence of 25-element sequences");
    return 0;
  }
  for (int s = 0; s < 2; ++s) {
    PyObject *row = PySequence_GetItem(obj, s);
    if (!PySequence_Check(row) || PySequence_Size(row) != 25) {
      Py_XDECREF(row);
      PyErr_SetString(PyExc_ValueError, "Each side must be length 25");
      return 0;
    }
    for (int p = 0; p < 25; ++p) {
      PyObject *v = PySequence_GetItem(row, p);
      int32_t x = static_cast<int32_t>(PyLong_AsLong(v));
      board[s][p] = static_cast<int>(x);
      Py_DECREF(v);
    }
    Py_DECREF(row);
  }
  return 1;
}

static PyObject *py_boardfromid(PyObject *self, PyObject *args) {
  const char *pos_id;
  if (!PyArg_ParseTuple(args, "s", &pos_id)) {
    return NULL;
  }

  int board[2][25] = {{0}};
  PositionFromID(board, pos_id);

  PyObject *outer = PyList_New(2);
  for (int s = 0; s < 2; ++s) {
    PyObject *inner = PyList_New(25);
    for (int p = 0; p < 25; ++p) {
      PyList_SetItem(inner, p, PyLong_FromLong(board[s][p]));
    }
    PyList_SetItem(outer, s, inner);
  }

  return outer;
}

// Helper: Convert Python list to C int array
bool PyList_ToBoard(PyObject *listObj, int board[2][25]) {
  if (!PyList_Check(listObj) || PyList_Size(listObj) != 2)
    return false;

  for (int s = 0; s < 2; ++s) {
    PyObject *side = PyList_GetItem(listObj, s);
    if (!PyList_Check(side) || PyList_Size(side) != 25)
      return false;

    for (int p = 0; p < 25; ++p) {
      PyObject *val = PyList_GetItem(side, p);
      board[s][p] = PyLong_AsLong(val);
    }
  }
  return true;
}

static PyObject *py_classify(PyObject *self, PyObject *args) {
  PyObject *boardObj;
  if (!PyArg_ParseTuple(args, "O", &boardObj))
    return NULL;

  int board[2][25];
  if (!PyList_ToBoard(boardObj, board)) {
    PyErr_SetString(PyExc_ValueError, "Expected 2x25 board list");
    return NULL;
  }

  int cls = ClassifyPosition(board);
  return PyLong_FromLong(cls);
}

static PyObject *py_pubbestmove(PyObject *self, PyObject *args) {
  PyObject *boardObj;
  int dice0, dice1;
  if (!PyArg_ParseTuple(args, "Oii", &boardObj, &dice0, &dice1))
    return NULL;

  int board[2][25];
  int move[8] = {0};

  if (!PyList_ToBoard(boardObj, board)) {
    PyErr_SetString(PyExc_ValueError, "Expected 2x25 board list");
    return NULL;
  }

  int n = FindPubevalMove(dice0, dice1, board, move);
  if (n < 0) {
    PyErr_SetString(PyExc_RuntimeError, "No valid move found");
    return NULL;
  }

  PyObject *result = PyList_New(n);
  for (int i = 0; i < n; ++i) {
    PyList_SetItem(result, i, PyLong_FromLong(move[i]));
  }
  return result;
}

static PyObject *py_pubevalscore(PyObject *self, PyObject *args) {
  PyObject *boardObj;
  if (!PyArg_ParseTuple(args, "O", &boardObj))
    return NULL;

  int board[2][25];
  if (!PyList_ToBoard(boardObj, board)) {
    PyErr_SetString(PyExc_ValueError, "Expected 2x25 board list");
    return NULL;
  }

  int fRace = ClassifyPosition(board) <= CLASS_RACE;
  float score = pubEvalVal(fRace, board);

  return PyFloat_FromDouble(score);
}

static PyObject *py_id(PyObject *self, PyObject *args) {
  PyObject *boardObj;
  if (!PyArg_ParseTuple(args, "O", &boardObj))
    return NULL;

  int board[2][25];
  if (!PyList_ToBoard(boardObj, board)) {
    PyErr_SetString(PyExc_ValueError, "Expected 2x25 board list");
    return NULL;
  }

  const char *id = PositionID(board);
  return PyUnicode_FromString(id);
}

static PyObject *py_rolldice(PyObject *self, PyObject *args) {
  int dice[2];
  RollDice(dice);
  return Py_BuildValue("ii", dice[0], dice[1]);
}

static PyObject *py_bestmove(PyObject * /*self*/, PyObject *args,
                             PyObject *kwargs) {
  // args/kwargs locals
  int board_arr[2][25];
  int dice1, dice2;
  int nPlies = 0;
  char side = 0;
  int moveBoard = 0;
  int resignInfo = 0;
  int listMoves = 0;
  int reduced = 0;

  static const char *kwlist[] = {"pos", "dice1", "dice2", "n",       "s",
                                 "b",   "r",     "list",  "reduced", NULL};

  if (!PyArg_ParseTupleAndKeywords(
          args, kwargs, "O&ii|iciiii", const_cast<char **>(kwlist), anyBoard,
          board_arr, &dice1, &dice2, &nPlies, &side, &moveBoard, &resignInfo,
          &listMoves, &reduced)) {
    return NULL;
  }

  // Validate inputs
  if (nPlies < 0) {
    PyErr_SetString(PyExc_ValueError, "negative ply");
    return NULL;
  }
  if (dice1 < 0 || dice1 > 6 || dice2 < 0 || dice2 > 6) {
    PyErr_SetString(PyExc_ValueError, "invalid dice");
    return NULL;
  }

  bool xOnPlay;
  switch (side) {
  case 'X':
  case 'x':
    xOnPlay = true;
    break;
  case 'O':
  case 'o':
    xOnPlay = false;
    break;
  case 0:
    xOnPlay = false;
    break;  // default
  default:
    PyErr_SetString(PyExc_ValueError, "invalid side");
    return NULL;
  }

  std::vector<MoveRecord> *recs = nullptr;
  if (listMoves)
    recs = new std::vector<MoveRecord>;

  int move_buf[8];
  int n = findBestMove(move_buf, dice1, dice2, board_arr, xOnPlay, nPlies, recs,
                       reduced);

  // pack the primary move‐tuple
  PyObject *moves = PyTuple_New(n / 2);
  for (int j = 0; j < n / 2; ++j) {
    int k = 2 * j;
    int from = move_buf[k] >= 0 ? move_buf[k] + 1 : 0;
    int to = move_buf[k + 1] >= 0 ? move_buf[k + 1] + 1 : 0;
    PyObject *mv2 = PyTuple_New(2);
    PyTuple_SET_ITEM(mv2, 0, PyLong_FromLong(from));
    PyTuple_SET_ITEM(mv2, 1, PyLong_FromLong(to));
    PyTuple_SET_ITEM(moves, j, mv2);
  }

  // if no extra info requested, return just that
  if (!moveBoard && !resignInfo && !listMoves) {
    delete recs;
    return moves;
  }

  // otherwise build the result tuple
  int extra = moveBoard + resignInfo + listMoves;
  PyObject *result = PyTuple_New(1 + extra);
  PyTuple_SET_ITEM(result, 0, moves);

  int idx = 1;

  // 1) new board?
  if (moveBoard) {
    SwapSides(board_arr);
    PyObject *bstr = PyUnicode_FromString(boardString(board_arr));
    PyTuple_SET_ITEM(result, idx++, bstr);
    SwapSides(board_arr);
  }

  // 2) resign info?
  if (resignInfo) {
    int r = 0;
    if (isRace(board_arr)) {
      AnalyzeBoard b;  // your short‐hand 26‐element array
      setBoard(b, board_arr);
      r = analyzer.offerResign(nPlies, 2, b, true);
    }
    PyTuple_SET_ITEM(result, idx++, PyLong_FromLong(r));
  }

  // 3) full move list?
  if (listMoves) {
    PyObject *listT = PyTuple_New(recs->size());
    for (size_t i = 0; i < recs->size(); ++i) {
      const auto &ri = (*recs)[i];
      PyObject *entry = PyTuple_New(4);

      // position key
      PyTuple_SET_ITEM(entry, 0, PyUnicode_FromString(posString(ri.pos)));

      // the individual move steps
      const int *mv = ri.move;
      int cnt = 0;
      while (cnt < 4 && mv[2 * cnt] >= 0)
        ++cnt;
      PyObject *mvsteps = PyTuple_New(2 * cnt);
      for (int j = 0; j < cnt; ++j) {
        int f = mv[2 * j] >= 0 ? mv[2 * j] + 1 : 0;
        int t = mv[2 * j + 1] >= 0 ? mv[2 * j + 1] + 1 : 0;
        PyTuple_SET_ITEM(mvsteps, 2 * j, PyLong_FromLong(f));
        PyTuple_SET_ITEM(mvsteps, 2 * j + 1, PyLong_FromLong(t));
      }
      PyTuple_SET_ITEM(entry, 1, mvsteps);

      // probabilities array
      PyObject *probs = PyTuple_New(5);
      for (int k = 0; k < 5; ++k) {
        PyTuple_SET_ITEM(probs, k, PyFloat_FromDouble(ri.probs[k]));
      }
      PyTuple_SET_ITEM(entry, 2, probs);

      // match‐score
      PyTuple_SET_ITEM(entry, 3, PyFloat_FromDouble(ri.matchScore));

      PyTuple_SET_ITEM(listT, i, entry);
    }
    PyTuple_SET_ITEM(result, idx++, listT);
    delete recs;
  }

  return result;
}

// ------------------------------------------------------------------
// keyofboard(pos: sequence) -> str
static PyObject *py_keyofboard(PyObject * /*self*/, PyObject *args) {
  int board_arr[2][25];
  // anyBoard will fill our 2×25 array from a Python sequence
  if (!PyArg_ParseTuple(args, "O&", anyBoard, board_arr)) {
    return NULL;
  }
  // boardString returns the 20-char A–Z key
  const char *key = boardString(board_arr);
  return PyUnicode_FromString(key);
}

//-----------------------------------------------------------------------------
// Python wrapper: boardfromkey(key: str) -> ((25,), (25,))
static PyObject *py_boardfromkey(PyObject * /*self*/, PyObject *args) {
  const char *key;
  if (!PyArg_ParseTuple(args, "s", &key))
    return NULL;

  int board[2][25];
  if (!stringToBoard(key, board)) {
    PyErr_SetString(PyExc_ValueError, "invalid board key");
    return NULL;
  }
  return pack_board(board);
}

//-----------------------------------------------------------------------------
// Converter: read either an int or a 6-tuple of bearoff points, producing
// a single bearoff-ID in *pi.
static int readBearoffId(PyObject *obj, void *pi) {
  int *out = static_cast<int *>(pi);

  // Case 1: a simple integer
  if (PyLong_Check(obj)) {
    int32_t v = static_cast<int32_t>(PyLong_AsLong(obj));
    if (!(1 <= v && v < 54264)) {
      PyErr_SetString(PyExc_ValueError,
                      "bearoff id outside of range [1,54264)");
      return 0;
    }
    *out = static_cast<int>(v);
    return 1;
  }

  // Case 2: a length-6 sequence of pip-counts
  if (PySequence_Check(obj) && PySequence_Size(obj) == 6) {
    PyObject *seq = PySequence_Fast(obj, "expected sequence of length 6");
    if (!seq)
      return 0;

    int p[6];
    for (int k = 0; k < 6; ++k) {
      PyObject *item = PySequence_Fast_GET_ITEM(seq, k);
      int32_t x = static_cast<int32_t>(PyLong_AsLong(item));
      if (PyErr_Occurred()) {
        Py_DECREF(seq);
        return 0;
      }
      p[k] = static_cast<int>(x);
    }
    Py_DECREF(seq);

    *out = PositionBearoff(p);
    return 1;
  }

  PyErr_SetString(
      PyExc_TypeError,
      "invalid type for bearoff id (int or len-6 sequence required)");
  return 0;
}

static PyObject *py_bearoffid2pos(PyObject * /*self*/, PyObject *args) {
  int id;
  // O& with readBearoffId picks up either an integer or a length-6 sequence
  if (!PyArg_ParseTuple(args, "O&", readBearoffId, &id)) {
    return NULL;  // parse error
  }

  int p[6];
  // Fills p[0]..p[5] from the GNUBG bearoff DB
  PositionFromBearoff(p, id);

  // Build a 6-tuple of ints
  return Py_BuildValue("(iiiiii)", p[0], p[1], p[2], p[3], p[4], p[5]);
}

//-----------------------------------------------------------------------------
// Python–3 binding for bearoff probabilities:
//   bearoffprobs(id_or_6tuple) -> tuple of floats
static PyObject *py_bearoffprobs(PyObject * /*self*/, PyObject *args) {
  int id;
  // readBearoffId handles either an integer or a 6-element tuple
  if (!PyArg_ParseTuple(args, "O&", readBearoffId, &id)) {
    return NULL;
  }

  // B is GNUBG’s bearoff‐prob struct:
  B b;
  getBearoff(id, &b);

  // number of leading zeros:
  Py_ssize_t zeros = (Py_ssize_t)(b.start - 1);
  Py_ssize_t total = zeros + (Py_ssize_t)b.len;
  PyObject *tup = PyTuple_New(total);
  if (!tup)
    return NULL;

  // fill leading zeros
  for (Py_ssize_t k = 0; k < zeros; ++k) {
    PyTuple_SET_ITEM(tup, k, PyFloat_FromDouble(0.0f));
  }
  // fill the actual probabilities
  for (unsigned int k = 0; k < b.len; ++k) {
    PyTuple_SET_ITEM(tup, zeros + (Py_ssize_t)k, PyFloat_FromDouble(b.p[k]));
  }
  return tup;
}

//-----------------------------------------------------------------------------
// moves(board, die1, die2, verbose=0) -> tuple of move-strings or
// (string,tuple) pairs
static PyObject *py_moves(PyObject * /*self*/, PyObject *args) {
  int board_arr[2][25];
  int die1, die2;
  int verbose = 0;

  // parse: O& (anyBoard), ii, optionally one int
  if (!PyArg_ParseTuple(args, "O&ii|i", anyBoard, board_arr, &die1, &die2,
                        &verbose)) {
    return NULL;
  }

  // generate the moves
  movelist ml;
  GenerateMoves(&ml, board_arr, die1, die2);

  // build the result tuple
  PyObject *out = PyTuple_New(ml.cMoves);
  if (!out)
    return NULL;

  for (unsigned int k = 0; k < (unsigned int)ml.cMoves; ++k) {
    const move &mv = ml.amMoves[k];
    const char *key = posString(mv.auch);

    if (!verbose) {
      // just the 20-char key
      PyTuple_SET_ITEM(out, k, PyUnicode_FromString(key));
    } else {
      // build the moves‐tuple for this entry
      unsigned int n = 0;
      while (n < 8 && mv.anMove[n] >= 0)
        n += 2;

      PyObject *mvSteps = PyTuple_New(n / 2);
      for (unsigned int j = 0; j < n / 2; ++j) {
        int from = mv.anMove[2 * j] >= 0 ? mv.anMove[2 * j] + 1 : 0;
        int to = mv.anMove[2 * j + 1] >= 0 ? mv.anMove[2 * j + 1] + 1 : 0;
        PyObject *pair = PyTuple_New(2);
        PyTuple_SET_ITEM(pair, 0, PyLong_FromLong(from));
        PyTuple_SET_ITEM(pair, 1, PyLong_FromLong(to));
        PyTuple_SET_ITEM(mvSteps, j, pair);
      }

      // package (key, mvSteps)
      PyObject *entry = PyTuple_New(2);
      PyTuple_SET_ITEM(entry, 0, PyUnicode_FromString(key));
      PyTuple_SET_ITEM(entry, 1, mvSteps);

      PyTuple_SET_ITEM(out, k, entry);
    }
  }

  return out;
}

//-----------------------------------------------------------------------------
// probs(board, nPlies, nr=1296) -> 5‐tuple of floats
static PyObject *py_probs(PyObject * /*self*/, PyObject *args) {
  int board_arr[2][25];
  int nPlies;
  unsigned int nr = 1296;

  // note: "O&O&|I"  →  two converter slots, then optional unsigned‐int
  if (!PyArg_ParseTuple(args, "O&O&|I", anyBoard, board_arr, readPly, &nPlies,
                        &nr)) {
    return NULL;
  }

  float p[5];
  switch (nPlies) {
  case PLY_OSR:
    if (!isRace(board_arr)) {
      PyErr_SetString(PyExc_RuntimeError, "Not a race position");
      return NULL;
    }
    raceProbs(board_arr, p, nr);
    break;
  case PLY_BEAROFF:
    EvaluatePositionToBO(board_arr, p, false);
    break;
  case PLY_PRUNE:
    evalPrune(board_arr, p);
    break;
  case PLY_1SBEAR:
    EvalBearoffOneSided(board_arr, p);
    break;
  case PLY_RACENET:
    NetEvalRace(board_arr, p);
    break;
  case PLY_1ANDHALF: {
    float p1[5];
    EvaluatePosition(board_arr, p, 0, 0, 0, 0, 0, 0);
    EvaluatePosition(board_arr, p1, 1, 0, 0, 0, 0, 0);
    for (int k = 0; k < 5; ++k)
      p[k] = 0.5f * (p[k] + p1[k]);
    break;
  }
  case PLY_1SRACE:
#if defined(OS_BEAROFF_DB)
    if (!EvalOSrace(board_arr, p)) {
      PyErr_SetString(PyExc_RuntimeError, "can't eval OS race DB");
      return NULL;
    }
    break;
#else
    PyErr_SetString(PyExc_RuntimeError, "OS race DB not available");
    return NULL;
#endif
  default:
    EvaluatePosition(board_arr, p, nPlies, 0, 0, 0, 0, 0);
    break;
  }

  PyObject *out = PyTuple_New(5);
  if (!out)
    return NULL;
  for (int k = 0; k < 5; ++k) {
    PyTuple_SET_ITEM(out, k, PyFloat_FromDouble(p[k]));
  }
  return out;
}

//-----------------------------------------------------------------------------
// rollout(pos, ngames=1296, n=0, level=Analyze::AUTO, nt=500, std=0)
//    -> (p0,p1,p2,p3,p4)  or  ((p0..p4),(ars0..ars4))
static PyObject *py_rollout(PyObject * /*self*/, PyObject *args,
                            PyObject *kwargs) {
  // our 26-element board rep (signed short)
  AnalyzeBoard board;

  // defaults
  int cGames = 1296;
  int nPlies = 0;
  Analyze::RolloutEndsAt level = Analyze::AUTO;
  int nTruncate = 500;
  int wantSts = 0;

  static const char *kwlist[] = {"pos", "ngames", "n", "level",
                                 "nt",  "std",    NULL};

  if (!PyArg_ParseTupleAndKeywords(
          args, kwargs,
          "O&|iiiii",  // one converter + 5 optional ints
          const_cast<char **>(kwlist),
          anyAnalyzeBoard,  // fills board[]
          &cGames, &nPlies, &level, &nTruncate, &wantSts)) {
    return NULL;
  }

  if (cGames <= 0) {
    PyErr_Format(PyExc_ValueError, "Invalid number of games (%d)", cGames);
    return NULL;
  }

  float p[NUM_OUTPUTS];
  float ars[NUM_OUTPUTS];

  // run the rollout
  analyzer.rollout(board,
                   /*money=*/false, p, ars, nPlies, nTruncate, cGames, level);

  // if std==0, return just the p[5]
  if (!wantSts) {
    return Py_BuildValue("ddddd", static_cast<double>(p[0]),
                         static_cast<double>(p[1]), static_cast<double>(p[2]),
                         static_cast<double>(p[3]), static_cast<double>(p[4]));
  }

  // otherwise return ((p0..p4),(ars0..ars4))
  return Py_BuildValue("((ddddd)(ddddd))", static_cast<double>(p[0]),
                       static_cast<double>(p[1]), static_cast<double>(p[2]),
                       static_cast<double>(p[3]), static_cast<double>(p[4]),
                       static_cast<double>(ars[0]), static_cast<double>(ars[1]),
                       static_cast<double>(ars[2]), static_cast<double>(ars[3]),
                       static_cast<double>(ars[4]));
}

//-----------------------------------------------------------------------------
// cubefullRollout(pos, ngames=576, side='X', ply=0) -> 13-element tuple of
// floats
static PyObject *py_cubefullRollout(PyObject * /*self*/, PyObject *args,
                                    PyObject *kwargs) {
  // Define default values for the arguments
  int nGames = 576;
  int nPlies = 0;
  char side = 'X';

  // Board representation
  AnalyzeBoard board;

  // Define the list of keywords for the argument parsing
  static const char *kwlist[] = {"pos", "ngames", "side", "ply", NULL};

  // Parse the input arguments
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O&|ci",
                                   const_cast<char **>(kwlist), anyAnalyzeBoard,
                                   board, &nGames, &side, &nPlies)) {
    return NULL;
  }

  // Check the side input and set the flag for which player is on play
  bool xOnPlay = false;
  switch (side) {
  case 'X':
  case 'x':
    xOnPlay = true;
    break;
  case 'O':
  case 'o':
    xOnPlay = false;
    break;
  default:
    PyErr_SetString(PyExc_ValueError, "Invalid side. Expected 'X' or 'O'.");
    return NULL;
  }

  // Set the board to the Analyze structure
  Analyze::GNUbgBoard anBoard;
  Analyze::set(board, anBoard, xOnPlay);

  // Perform the rollout
  const float *result =
      analyzer.rolloutCubefull(anBoard, nPlies, nGames, xOnPlay);

  // Prepare the result tuple with 13 floats
  PyObject *tuple = PyTuple_New(13);
  if (!tuple)
    return NULL;

  // Fill the tuple with the values from the result array
  for (int i = 0; i < 13; ++i) {
    PyTuple_SET_ITEM(tuple, i, PyFloat_FromDouble(result[i]));
  }

  return tuple;
}

static PyObject *py_set_equities(PyObject * /*self*/, PyObject *const args) {
  const char *which;

  // Case 1: One argument (string)
  if (PyTuple_Size(args) == 1) {
    if (!PyArg_ParseTuple(args, "s", &which)) {
      return NULL;
    }

    if (strcasecmp("gnur", which) == 0) {
      Equities::set(Equities::gnur);
    } else if (strcasecmp("jacobs", which) == 0) {
      Equities::set(Equities::Jacobs);
    } else if (strcasecmp("woolsey", which) == 0) {
      Equities::set(Equities::WoolseyHeinrich);
    } else if (strcasecmp("snowie", which) == 0) {
      Equities::set(Equities::Snowie);
    } else if (strcasecmp("mec26", which) == 0) {
      Equities::set(Equities::mec26);
    } else if (strcasecmp("mec57", which) == 0) {
      Equities::set(Equities::mec57);
    } else {
      PyErr_SetString(PyExc_RuntimeError, "Not a valid equities table name");
      return NULL;
    }
  } else if (PyTuple_Size(args) == 2) {  // Case 2: Two arguments (doubles for
                                         // weights and growth rates)
    double w, gr;
    if (!PyArg_ParseTuple(args, "dd", &w, &gr)) {
      return NULL;
    }

    if (!(w > 0.0f && w < 1.0f && gr > 0.0f && gr < 1.0f)) {
      PyErr_SetString(PyExc_ValueError,
                      "Weights and growth rates must be in [0, 1] range");
      return NULL;
    }

    Equities::set(w, gr);
  } else {
    // Wrong number of arguments
    PyErr_SetString(
        PyExc_TypeError,
        "Expected either one string or two floats (weight, growth_rate)");
    return NULL;
  }

  // Return None (success)
  Py_INCREF(Py_None);
  return Py_None;
}

// Seed function
static PyObject *set_seed(PyObject *self, PyObject *args) {
  uint64_t seed;
  if (!PyArg_ParseTuple(args, "l", &seed)) {
    return NULL;
  }

  // Set the seed in the random number generator
  Analyze::srandom(seed);

  Py_INCREF(Py_None);
  return Py_None;
}

// Shortcuts function
static PyObject *set_shortcuts(PyObject *self, PyObject *args) {
  int use;
  if (!PyArg_ParseTuple(args, "i", &use)) {
    return NULL;
  }

  // Enable or disable evaluation shortcuts
  setShortCuts(use);

  Py_INCREF(Py_None);
  return Py_None;
}

// Enable/Disable OS database function
static PyObject *set_osdb(PyObject *self, PyObject *args) {
  int use;
  if (!PyArg_ParseTuple(args, "i", &use)) {
    return NULL;
  }

  // Enable or disable the OS database
  if (use) {
    enableOSdb();
  } else {
    disableOSdb();
  }

  Py_INCREF(Py_None);
  return Py_None;
}

// Set move filters function
static PyObject *set_ps(PyObject *self, PyObject *args) {
  int nPlies, nMoves, nAdditional;
  double threshold;
  if (!PyArg_ParseTuple(args, "iiid", &nPlies, &nMoves, &nAdditional,
                        &threshold)) {
    return NULL;
  }

  // Set the move filters
  setPlyBounds(nPlies, nMoves, nAdditional, threshold);

  Py_INCREF(Py_None);
  return Py_None;
}

// Set match score function
static PyObject *set_score(PyObject *self, PyObject *args) {
  int usAway, opAway, crawford = 0;
  if (!PyArg_ParseTuple(args, "ii|i", &usAway, &opAway, &crawford)) {
    return NULL;
  }

  if (usAway < 0 || opAway < 0 || (crawford < 0 || crawford > 1)) {
    return NULL;
  }

  if (crawford == 1 &&
      !((opAway == 1 && usAway > 1) || (opAway > 1 && usAway == 1))) {
    PyErr_SetString(PyExc_RuntimeError, "Away not compatible with crawford");
    return NULL;
  }

  // Set the match score in the analyzer
  analyzer.setScore(opAway, usAway);
  analyzer.crawford(crawford);

  Py_INCREF(Py_None);
  return Py_None;
}

// Set match cube function
static PyObject *set_cube(PyObject *self, PyObject *args) {
  int cube;
  char x = 0;
  if (!PyArg_ParseTuple(args, "i|c", &cube, &x)) {
    return NULL;
  }

  if (cube <= 0) {
    return NULL;
  }

  bool xOwn = false;
  if (cube > 1) {
    if (x == 0) {
      return NULL;
    }

    if (tolower(x) == 'x') {
      xOwn = true;
    } else if (tolower(x) == 'o') {
      xOwn = false;
    } else {
      return NULL;
    }
  }

  // Set the cube in the analyzer
  analyzer.setCube(cube, xOwn);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *equities_value(PyObject * /*self*/, PyObject *const args) {
  int xAway, oAway;

  if (!PyArg_ParseTuple(args, "ii", &xAway, &oAway)) {
    return NULL;
  }

  if (!(0 <= xAway && xAway <= 25 && 0 <= oAway && oAway <= 25)) {
    PyErr_SetString(PyExc_ValueError, "Score not in 0-25 range");
    return NULL;
  }

  // Call the Equities class static method to get the value
  float v = Equities::value(xAway, oAway);

  return PyFloat_FromDouble(v);
}

static PyObject *py_onecrace(PyObject *, PyObject *const args) {
  int n;

  // Parse the argument (an integer)
  if (!PyArg_ParseTuple(args, "i", &n)) {
    return NULL;
  }

  float stdv;
  float v = ocr(n, &stdv);  // Call the ocr function

  if (v == 0.0f) {
    return NULL;  // If OCR returns 0.0f, we return None
  }

  // Return the result as a tuple of two floats (v and stdv)
  return Py_BuildValue("dd", v, stdv);
}

extern float centeredLDweight, ownedLDweight;
extern bool useRaceMagic;

static PyObject *py_evaluate_cube_decision(PyObject *self, PyObject *args,
                                           PyObject *kwargs) {
  if (Equities::match.xAway == 0 && Equities::match.oAway == 0) {
    PyErr_SetString(PyExc_RuntimeError, "Not implemented for money");
    return 0;
  }

  int nPlies = 0;
  int nPliesVerify = -1;
  double ad = 0.5;

  char side = 0;
  int verboseInfo = 0;
  PyObject *p = 0;

  float const s_centeredLDweight = centeredLDweight;
  float const s_ownedLDweight = ownedLDweight;
  float probs[5];
  probs[0] = -1;

  bool APopt = true;
  bool APshortcuts = false;

  AnalyzeBoard board;

  static const char *kwlist[] = {"pos", "n", "v", "s", "i", "p", 0};

  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O&|iiciO",
                                   const_cast<char **>(kwlist),
                                   &anyAnalyzeBoard, &board, &nPlies,
                                   &nPliesVerify, &side, &verboseInfo, &p)) {
    return 0;
  }

  bool xOnPlay = false;

  switch (side) {
  case 'X':
  case 'x':
    xOnPlay = true;
    break;
  case 'O':
  case 'o':
    xOnPlay = false;
    break;
  case 0:
    break;
  default: {
    PyErr_SetString(PyExc_ValueError, "invalid side");
    return 0;
  }
  }

  if (Equities::match.cube > 1 && Equities::match.xOwns != xOnPlay) {
    PyErr_Format(PyExc_RuntimeError, "side (%c) does not own cube", side);
    return 0;
  }

  if (p) {
    if (!(PySequence_Check(p) && PySequence_Size(p) == 5)) {
      PyErr_SetString(PyExc_ValueError, "invalid probablities");
      return 0;
    }

    for (uint k = 0; k < 5; ++k) {
      PyObject *const pk = PySequence_Fast_GET_ITEM(p, k);
      probs[k] = PyFloat_AsDouble(pk);
      if (!(0 <= probs[k] && probs[k] <= 1)) {
        PyErr_SetString(PyExc_ValueError, "invalid probablities");
        return 0;
      }
    }
  }

  Analyze::nPliesToDouble = nPlies;

  if (nPliesVerify < 0) {
    nPliesVerify = (nPlies == 0 ? 0 : 2);
  }

  Analyze::nPliesToDoubleVerify = nPliesVerify;

  Player::R1 const &info = analyzer.rollOrDouble(
      board, xOnPlay, ad, APopt, APshortcuts, probs[0] >= 0 ? probs : 0);

  centeredLDweight = s_centeredLDweight;
  ownedLDweight = s_ownedLDweight;

  if (verboseInfo) {
    PyObject *const v =
        Py_BuildValue("iiiddd", info.actionDouble, info.actionTake,
                      info.tooGood, info.matchProbNoDouble,
                      info.matchProbDoubleTake, info.matchProbDoubleDrop);
    return v;
  }

  return PyLong_FromLong(info.actionDouble);
}

static PyMethodDef GnubgMethods[] = {
    {"classify", py_classify, METH_VARARGS, "Classify a board position."},
    {"pub_best_move", py_pubbestmove, METH_VARARGS,
     "Get best move using public evaluation."},
    {"board_from_position_id", py_boardfromid, METH_VARARGS,
     "Convert a GNUBG Position ID to a board list"},
    {"board_from_position_key", (PyCFunction)py_boardfromkey, METH_VARARGS,
     "boardfromkey(key: str) -> (two 25-tuples)"},
    {"key_of_board", py_keyofboard, METH_VARARGS,
     "keyofboard(board) -> position key string"},
    {"position_id", py_id, METH_VARARGS,
     "Convert board to Position ID (base64)"},
    {"pub_eval_score", py_pubevalscore, METH_VARARGS,
     "Public evaluation score for the board"},
    {"roll", py_rolldice, METH_VARARGS, "Roll two dice (uses GNUBG RNG)"},
    {"best_move", (PyCFunction)py_bestmove, METH_VARARGS | METH_KEYWORDS,
     "bestmove(pos, dice1, dice2, n=0, s=0, b=0, r=0, list=0, reduced=0)\n"
     "Returns either a tuple of moves, or (moves, board?, resign?, list?)."},
    {"bearoff_id_2_pos", py_bearoffid2pos, METH_VARARGS,
     "bearoffid2pos(id) -> tuple of 6 ints giving the bearoff position"},
    {"bearoff_probabilities", py_bearoffprobs, METH_VARARGS,
     "bearoffprobs(id_or_6tuple) → tuple of bearoff probabilities"},
    {"moves", py_moves, METH_VARARGS,
     "moves(board, die1, die2, verbose=0) → tuple of move-keys or (key,steps) "
     "pairs"},
    {"probabilities", py_probs, METH_VARARGS,
     "probs(board, nPlies, nr=1296)\n\n"
     "Evaluate a position:\n"
     " - board: 2×25 list\n"
     " - nPlies: one of the PLY_* constants\n"
     " - nr: roll count for OSR\n\n"
     "Returns a 5‐tuple of floats (win, gamm, backgammon, etc.)"},
    {"rollout", (PyCFunction)py_rollout, METH_VARARGS | METH_KEYWORDS,
     "rollout(pos, ngames=1296, n=0, level, nt=500, std=0)\n"
     "Perform a rollout:\n"
     "  pos    : 26-element list or key\n"
     "  ngames : number of simulated games\n"
     "  n      : number of plies per rollout\n"
     "  level  : Analyze::AUTO|RACE|BEAROFF|OVER\n"
     "  nt     : truncation length\n"
     "  std    : if nonzero, also return stderr array\n\n"
     "Returns a 5-tuple of floats, or if std=1 a pair of 5-tuples."},
    {"cubeful_rollout", (PyCFunction)py_cubefullRollout,
     METH_VARARGS | METH_KEYWORDS,
     "cubefullRollout(pos, ngames=576, side='X', ply=0) -> 13-element tuple\n"
     "Simulate a set of cube rolls and return the results as 13 floats."},
    {"one_checker_race", py_onecrace, METH_VARARGS,
     "OCR function to compute value and standard deviation for a given "
     "number."},
    {"evaluate_cube_decision", (PyCFunction)py_evaluate_cube_decision,
     METH_VARARGS | METH_KEYWORDS,
     "evaluate_cube_decision(pos, n=0, v=-1, s='X', i=0, p=None)\n"
     "Evaluate whether to double, take/pass, or play on. Returns integer or "
     "verbose stats."},
    {NULL, NULL, 0, NULL}};

// Method table for the 'equities' submodule
static PyMethodDef gnubg_equities_methods[] = {
    {"value", equities_value, METH_VARARGS,
     "Get the equities value for a given position."},
    {NULL, NULL, 0, NULL}  // Sentinel to mark the end of the method table
};

// Create a PyModuleDef for the 'equities' submodule
static PyModuleDef gnubg_equities_module = {
    PyModuleDef_HEAD_INIT,  // Standard header for all Python modules
    "equities",             // Name of the submodule
    "Equities-related methods for GNUBG",  // Module docstring
    -1,                     // Size of the module, -1 means no state
    gnubg_equities_methods  // Method table
};

// Define the method table for the 'set' submodule
static PyMethodDef gnubg_set_methods[] = {
    {"seed", set_seed, METH_VARARGS, "Set internal random generator seed."},
    {"shortcuts", set_shortcuts, METH_VARARGS, "Set evaluation shortcuts."},
    {"osdb", set_osdb, METH_VARARGS, "Enable/Disable OS database"},
    {"ps", set_ps, METH_VARARGS, "Set move filters"},
    {"equities", py_set_equities, METH_VARARGS, "Set equities table to use"},
    {"score", set_score, METH_VARARGS, "Set match score"},
    {"cube", set_cube, METH_VARARGS, "Set match cube"},
    {NULL, NULL, 0, NULL}  // Sentinel to mark the end of the method table
};

// Define the 'set' submodule
static PyModuleDef gnubg_set_module = {
    PyModuleDef_HEAD_INIT,
    "set",                                          // Module name
    "Set various parameters for the GNUBG engine",  // Module docstring
    -1,                // Size of the module state, -1 means no state
    gnubg_set_methods  // Method table
};

static struct PyModuleDef gnubgmodule = {
    PyModuleDef_HEAD_INIT, "_gnubg_nn",
    "Python bindings for GNUBG neural net evaluation", -1, GnubgMethods};

//---------------------------------------------------------------------------
// Cross‐platform helper to locate the “data/” alongside the shared module.
static std::string find_data_dir(PyObject *module) {
#if defined(_WIN32)
  HMODULE h = NULL;
  // Get handle for this module
  if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                             GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                         (LPCSTR)&PyInit__gnubg_nn, &h)) {
    char buf[MAX_PATH];
    if (GetModuleFileNameA(h, buf, MAX_PATH)) {
      std::string path(buf);
      auto pos = path.find_last_of("\\/");
      return path.substr(0, pos) + "\\data";
    }
  }
  return ".";

#elif defined(__unix__) || defined(__APPLE__)
  Dl_info dl;
  // if (dladdr((void*)&find_data_dir, &dl) && dl.dli_fname) {
  if (dladdr(
          reinterpret_cast<void *>(reinterpret_cast<uintptr_t>(&find_data_dir)),
          &dl) &&
      dl.dli_fname) {
    char *dup = strdup(dl.dli_fname);
    std::string base = dirname(dup);
    free(dup);
    return base + "/data";
  }
  return ".";

#else
  // Fallback: Python’s __file__
  PyObject *fobj = PyModule_GetFilenameObject(module);
  if (!fobj) {
    PyErr_Clear();
    return ".";
  }
  const char *fname = PyUnicode_AsUTF8(fobj);
  Py_DECREF(fobj);
  if (!fname)
    return ".";
  char *dup = strdup(fname);
  std::string base = dirname(dup);
  free(dup);
  return base + "/data";
#endif
}

//---------------------------------------------------------------------------
// Module initialization
// cppcheck-suppress unusedFunction
PyMODINIT_FUNC PyInit__gnubg_nn(void) {
  // Initialize the module
  PyObject *m = PyModule_Create(&gnubgmodule);
  if (m == NULL) {
    return NULL;
  }

  // Create the 'equities' submodule
  PyObject *equities_module = PyModule_Create(&gnubg_equities_module);
  if (equities_module == NULL) {
    return NULL;
  }

  // Add the 'equities' submodule to the main module
  PyModule_AddObject(m, "equities", equities_module);

  // Create the 'set' submodule
  PyObject *set_module = PyModule_Create(&gnubg_set_module);
  if (set_module == NULL) {
    return NULL;
  }

  // Add the 'set' submodule to the main module
  PyModule_AddObject(m, "set", set_module);

  // Locate our shipped data directory
  std::string datadir = find_data_dir(m);
#ifndef _WIN32
  // on Unix we used forward‐slash
#else
  // on Win32 convert to forward‐slash for Analyze::init()
  std::replace(datadir.begin(), datadir.end(), '\\', '/');
#endif

  // If the user hasn't already pointed GNUBGHOME somewhere, default it
  if (!std::getenv("GNUBGHOME")) {
// third argument “1” means “always overwrite”, but since getenv was null
// this just sets it for our process before Analyze::init()
#if defined(_WIN32)
    // Overwrite GNUBGHOME in the current process
    _putenv_s("GNUBGHOME", datadir.c_str());
#else
    setenv("GNUBGHOME", datadir.c_str(), 1);
#endif
  }

  // Define paths to required data files
  std::string weights = datadir + "/gnubg.weights";
  // std::string os_bd   = datadir + "/gnubg_os.db";
  // std::string ts0_bd  = datadir + "/gnubg_ts0.bd";
  // std::string os0_bd  = datadir + "/gnubg_os0.bd";

  // Initialize GNUBG (loads all six nets into the global `nets[]`)
  if (!Analyze::init(weights.c_str())) {
    PyErr_SetString(PyExc_ImportError,
                    "Analyze::init() failed to load GNUBG neural nets");
    return NULL;
  }

  // Optional SSE optimizations
  useSSE(1);

  // Expose constants for CLASS_* categories
  PyModule_AddIntConstant(m, "c_over", CLASS_OVER);
  PyModule_AddIntConstant(m, "c_bearoff", CLASS_BEAROFF1);
  PyModule_AddIntConstant(m, "c_race", CLASS_RACE);
  PyModule_AddIntConstant(m, "c_crashed", CLASS_CRASHED);
#if defined(CONTAINMENT_CODE)
  PyModule_AddIntConstant(m, "c_backcontain", CLASS_BACKCONTAIN);
#endif
  PyModule_AddIntConstant(m, "c_contact", CLASS_CONTACT);

  // Expose constants for PLY_* categories
  PyModule_AddIntConstant(m, "p_osr", PLY_OSR);
  PyModule_AddIntConstant(m, "p_bearoff", PLY_BEAROFF);
  PyModule_AddIntConstant(m, "p_prune", PLY_PRUNE);
  PyModule_AddIntConstant(m, "p_1sbear", PLY_1SBEAR);
  PyModule_AddIntConstant(m, "p_race", PLY_RACENET);
  PyModule_AddIntConstant(m, "p_1srace", PLY_1SRACE);
  PyModule_AddIntConstant(m, "p_0plus1", PLY_1ANDHALF);

  // Expose constants for Analyze::RolloutEndsAt categories
  PyModule_AddIntConstant(m, "ro_race", Analyze::RACE);
  PyModule_AddIntConstant(m, "ro_bearoff", Analyze::BEAROFF);
  PyModule_AddIntConstant(m, "ro_over", Analyze::OVER);
  PyModule_AddIntConstant(m, "ro_auto", Analyze::AUTO);

  // Finally return the Python extension module
  return m;
}
