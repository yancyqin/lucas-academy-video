import {Composition} from 'remotion';
import {VG_WHY_DURATION, VG_WHY_FPS, VgWhyCover, VgWhyVideo} from './videos/vg-why/VgWhyVideo';
import {RD_FPS, filmDuration, LanguageBridgeCover, LanguageBridgeVideo, type LanguageBridgeProps} from './videos/ReciprocalDoorsVideo';
import {WP_FPS, WholePersonCover, WholePersonVideo, calculateWholePersonMetadata} from './videos/whole-person-01/WholePersonVideo';
import {FI_FPS, FunInformaticsCover, FunInformaticsVideo, calculateFunInformaticsMetadata} from './videos/fun-informatics-01/FunInformaticsVideo';
import {FunInformatics02Video, FunInformatics02Cover, FunInformatics02EnglishCover, calculateClaudeMetadata} from './videos/fun-informatics-02/FunInformatics02Video';
import {FunInformatics03Video, calculateNoiseMetadata} from './videos/fun-informatics-03/FunInformatics03Video';
import {FunEconomics01Video, FunEconomics01Cover, FunEconomics01CoverEn, calculateEconMetadata} from './videos/fun-economics-01/FunEconomics01Video';
import {FunEconomics01ExtraVideo, FunEconomics01ExtraCover, FunEconomics01ExtraCoverEn, calculateExtraMetadata} from './videos/fun-economics-01-7x8/FunEconomics01ExtraVideo';
import {FunEconomics02Video, FunEconomics02Cover, FunEconomics02CoverEn, calculateFe02Metadata} from './videos/fun-economics-02/FunEconomics02Video';
import {NewsEducation01Video, NewsEducation01Cover, NewsEducation01CoverEn, calculateNe01Metadata} from './videos/news-education-01/NewsEducation01Video';
import {WeeklyCover, WeeklyEpisode, calculateWeeklyMetadata} from './videos/weekly/WeeklyEpisode';
import {Cube2x2Cover, Cube2x2Video, calculateCubeMetadata} from './videos/cube-2x2/Cube2x2Video';
import type {FC} from 'react';
import {MonkeySocietyVideo} from './MonkeySocietyVideo';
import {MonkeyIntroVideo} from './videos/MonkeyIntroVideo';
import {
  ROLLER_COASTER_CHAT_DURATION,
  ROLLER_COASTER_CHAT_FPS,
  RollerCoasterChatVideo,
} from './videos/RollerCoasterChatVideo';
import introScript from './scripts/intro.en.json';
import {makeLyricsVideo, type Song} from './videos/LyricsVideo';
import oneBreath from './songs/one-breath.json';
import rejoice from './songs/rejoice.json';
import {
  ROLLER_COASTER_M2_DURATION,
  ROLLER_COASTER_M2_FPS,
  RollerCoasterMilestone2Video,
} from './videos/RollerCoasterMilestone2Video';
import {
  ROLLER_COASTER_SHORT_DURATION,
  ROLLER_COASTER_SHORT_FPS,
  RollerCoasterMilestonesShortVideo,
} from './videos/RollerCoasterMilestonesShortVideo';
import {
  ROLLER_COASTER_M3_BUILD_DURATION,
  ROLLER_COASTER_M3_BUILD_FPS,
  RollerCoasterMilestone3BuildVideo,
} from './videos/RollerCoasterMilestone3BuildVideo';
import {
  ROLLER_COASTER_M3_BUILD_VERTICAL_DURATION,
  ROLLER_COASTER_M3_BUILD_VERTICAL_FPS,
  RollerCoasterMilestone3BuildVerticalVideo,
} from './videos/RollerCoasterMilestone3BuildVerticalVideo';

const OneBreathVideo = makeLyricsVideo(oneBreath as Song);
const CHORUS_FROM = 84;
const CHORUS_SECONDS = 46;
const OneBreathChorus = makeLyricsVideo(oneBreath as Song, {offsetSeconds: CHORUS_FROM});

const RejoiceVideo = makeLyricsVideo(rejoice as Song);
/** Three cuts of the same film: lyrics low, lyrics centred, and pictures alone. */
const RejoiceCenter = makeLyricsVideo(rejoice as Song, {anchor: 'center'});
const RejoiceClean = makeLyricsVideo(rejoice as Song, {hideLyrics: true});
/** The cross section into the first chorus -- the part with the most to get wrong. */
const REJOICE_WINDOW_FROM = 41;
const REJOICE_WINDOW_SECONDS = 62;
const RejoiceWindow = makeLyricsVideo(rejoice as Song, {offsetSeconds: REJOICE_WINDOW_FROM});
/** The nail -> cross -> three crosses -> milky way run, on stills and stock only. */
const REJOICE_CROSS_FROM = 30;
const REJOICE_CROSS_SECONDS = 18;
const RejoiceCross = makeLyricsVideo(rejoice as Song, {offsetSeconds: REJOICE_CROSS_FROM});
/** First chorus: the silhouette, the clouds, the bubbles and the (Rejoice) echo. */
const REJOICE_C1_FROM = 66;
const REJOICE_C1_SECONDS = 38;
const RejoiceChorus1 = makeLyricsVideo(rejoice as Song, {offsetSeconds: REJOICE_C1_FROM});
/** A movable window for checking one stretch without paying for the whole film. */
const REJOICE_PROBE_FROM = 140;
const REJOICE_PROBE_SECONDS = 28;
// Centred, to match the version being delivered -- a probe is only useful for
// confirming a change if it is cut the same way as the film it stands in for.
const RejoiceProbe = makeLyricsVideo(rejoice as Song, {
  offsetSeconds: REJOICE_PROBE_FROM,
  anchor: 'center',
});
/** The last chorus: the only place the golden-light clip appears. */
const REJOICE_FINALE_FROM = 250;
const REJOICE_FINALE_SECONDS = 57;
const RejoiceFinale = makeLyricsVideo(rejoice as Song, {offsetSeconds: REJOICE_FINALE_FROM});

export const Root: FC = () => {
  return (
    <>
      <Composition
        id="Rejoice"
        component={RejoiceVideo}
        durationInFrames={Math.ceil(rejoice.durationSeconds * rejoice.fps)}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceCenter"
        component={RejoiceCenter}
        durationInFrames={Math.ceil(rejoice.durationSeconds * rejoice.fps)}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceClean"
        component={RejoiceClean}
        durationInFrames={Math.ceil(rejoice.durationSeconds * rejoice.fps)}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceWindow"
        component={RejoiceWindow}
        durationInFrames={REJOICE_WINDOW_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceCross"
        component={RejoiceCross}
        durationInFrames={REJOICE_CROSS_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceChorus1"
        component={RejoiceChorus1}
        durationInFrames={REJOICE_C1_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceProbe"
        component={RejoiceProbe}
        durationInFrames={REJOICE_PROBE_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceFinale"
        component={RejoiceFinale}
        durationInFrames={REJOICE_FINALE_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="OneBreathChorus"
        component={OneBreathChorus}
        durationInFrames={CHORUS_SECONDS * oneBreath.fps}
        fps={oneBreath.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="OneBreath"
        component={OneBreathVideo}
        durationInFrames={Math.ceil(oneBreath.durationSeconds * oneBreath.fps)}
        fps={oneBreath.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RollerCoasterMilestone1"
        component={RollerCoasterChatVideo}
        durationInFrames={ROLLER_COASTER_CHAT_DURATION}
        fps={ROLLER_COASTER_CHAT_FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="RollerCoasterMilestone2"
        component={RollerCoasterMilestone2Video}
        durationInFrames={ROLLER_COASTER_M2_DURATION}
        fps={ROLLER_COASTER_M2_FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="RollerCoasterMilestonesShort"
        component={RollerCoasterMilestonesShortVideo}
        durationInFrames={ROLLER_COASTER_SHORT_DURATION}
        fps={ROLLER_COASTER_SHORT_FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="RollerCoasterMilestone3Build"
        component={RollerCoasterMilestone3BuildVideo}
        durationInFrames={ROLLER_COASTER_M3_BUILD_DURATION}
        fps={ROLLER_COASTER_M3_BUILD_FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="RollerCoasterMilestone3BuildVertical"
        component={RollerCoasterMilestone3BuildVerticalVideo}
        durationInFrames={ROLLER_COASTER_M3_BUILD_VERTICAL_DURATION}
        fps={ROLLER_COASTER_M3_BUILD_VERTICAL_FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="MonkeyIntro"
        component={MonkeyIntroVideo}
        durationInFrames={introScript.durationSeconds * introScript.fps}
        fps={introScript.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="MonkeySociety"
        component={MonkeySocietyVideo}
        durationInFrames={432}
        fps={24}
        width={1920}
        height={1080}
      />
      {/* 梵高为什么画他们？ (lucas-academy-media#3): previews with each track, and the
          silent picture that scripts/vg-why/deliver.py muxes both tracks onto. */}
      {([
        ['VgWhyZh', {audio: 'zh'}],
        ['VgWhyEn', {audio: 'en'}],
        ['VgWhyPicture', {audio: 'none'}],
      ] as const).map(([id, props]) => (
        <Composition
          key={id}
          id={id}
          component={VgWhyVideo}
          defaultProps={props}
          durationInFrames={VG_WHY_DURATION}
          fps={VG_WHY_FPS}
          width={1920}
          height={1080}
        />
      ))}
      <Composition id="VgWhyCover" component={VgWhyCover} durationInFrames={1} fps={VG_WHY_FPS} width={1920} height={1080} />
      <Composition id="VgWhyCoverEn" component={VgWhyCover} defaultProps={{lang: 'en' as const}} durationInFrames={1} fps={VG_WHY_FPS} width={1920} height={1080} />
      {/* 语言的桥 · Language Bridge (lucas-academy-media#4): a Chinese film and an English film. */}
      {([
        ['LanguageBridgeZh', {lang: 'zh', audio: true, subtitles: true}],
        ['LanguageBridgeEn', {lang: 'en', audio: true, subtitles: true}],
        // Delivery pictures, muted (the mixed, loudness-matched narration is muxed in).
        // Clean = for YouTube with the SRT captions (the owner's choice); Subtitled = burned in
        // (Chinese film: Chinese + small English; English film: English only) for sharing elsewhere.
        ['LanguageBridgeZhClean', {lang: 'zh', audio: false, subtitles: false}],
        ['LanguageBridgeEnClean', {lang: 'en', audio: false, subtitles: false}],
        ['LanguageBridgeZhSubtitled', {lang: 'zh', audio: false, subtitles: true}],
        ['LanguageBridgeEnSubtitled', {lang: 'en', audio: false, subtitles: true}],
      ] as [string, LanguageBridgeProps][]).map(([id, props]) => (
        <Composition
          key={id}
          id={id}
          component={LanguageBridgeVideo}
          defaultProps={props}
          durationInFrames={filmDuration(props.lang)}
          fps={RD_FPS}
          width={1920}
          height={1080}
        />
      ))}
      {(['zh', 'en'] as const).map((lang) => (
        <Composition key={`lb-cover-${lang}`} id={lang === 'zh' ? 'LanguageBridgeCoverZh' : 'LanguageBridgeCoverEn'}
          component={LanguageBridgeCover} defaultProps={{lang}} durationInFrames={1} fps={RD_FPS} width={1920} height={1080} />
      ))}
      {/* 我们怎样陪孩子成长：全人教育的五个理念 (lucas-academy-media#5): one film per language, no burned-in captions. */}
      {(['zh', 'en'] as const).map((lang) => (
        <Composition
          key={lang}
          id={lang === 'zh' ? 'WholePersonZh' : 'WholePersonEn'}
          component={WholePersonVideo}
          defaultProps={{lang, tl: null}}
          calculateMetadata={calculateWholePersonMetadata}
          durationInFrames={1}
          fps={WP_FPS}
          width={1920}
          height={1080}
        />
      ))}
      {/* …and their YouTube covers (rendered by scripts/whole-person-01/youtube.py). */}
      {(['zh', 'en'] as const).map((lang) => (
        <Composition
          key={`cover-${lang}`}
          id={lang === 'zh' ? 'WholePersonCoverZh' : 'WholePersonCoverEn'}
          component={WholePersonCover}
          defaultProps={{lang}}
          durationInFrames={1}
          fps={WP_FPS}
          width={1920}
          height={1080}
        />
      ))}
      {/* Fun Informatics 1 · 计算机怎么算 1+1=？ / How Does a Computer Add 1 + 1=? (FUN-INFORMATICS-01.md): one film per language. */}
      {(['zh', 'en'] as const).map((lang) => (
        <Composition key={`fi01-${lang}`} id={lang === 'zh' ? 'FunInformatics01Zh' : 'FunInformatics01En'}
          component={FunInformaticsVideo} defaultProps={{lang, tl: null}} calculateMetadata={calculateFunInformaticsMetadata}
          durationInFrames={1} fps={FI_FPS} width={1920} height={1080} />
      ))}
      {(['zh', 'en'] as const).map((lang) => (
        <Composition key={`fi01-cover-${lang}`} id={lang === 'zh' ? 'FunInformatics01CoverZh' : 'FunInformatics01CoverEn'}
          component={FunInformaticsCover} defaultProps={{lang}} durationInFrames={1} fps={FI_FPS} width={1920} height={1080} />
      ))}
      <Composition id="FunInformatics02Zh" component={FunInformatics02Video} durationInFrames={24000} fps={30} width={1920} height={1080} defaultProps={{tl:null}} calculateMetadata={calculateClaudeMetadata} />
      <Composition id="FunInformatics02En" component={FunInformatics02Video} durationInFrames={24000} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"en"}} calculateMetadata={calculateClaudeMetadata} />
      <Composition id="FunInformatics02CoverZh" component={FunInformatics02Cover} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="FunInformatics02CoverEn" component={FunInformatics02EnglishCover} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="FunInformatics03Zh" component={FunInformatics03Video} durationInFrames={12000} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"zh"}} calculateMetadata={calculateNoiseMetadata} />
      <Composition id="FunInformatics03En" component={FunInformatics03Video} durationInFrames={12000} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"en"}} calculateMetadata={calculateNoiseMetadata} />
      {/* "How Do You Solve a 2×2 Cube?" (CUBE-2X2.md): one picture; English narration, and the Chinese track to preview */}
      <Composition id="Cube2x2" component={Cube2x2Video} durationInFrames={12000} fps={30} width={1920} height={1080} defaultProps={{tl:null,track:"en" as const}} calculateMetadata={calculateCubeMetadata} />
      <Composition id="Cube2x2ZhTrack" component={Cube2x2Video} durationInFrames={12000} fps={30} width={1920} height={1080} defaultProps={{tl:null,track:"zh" as const}} calculateMetadata={calculateCubeMetadata} />
      <Composition id="Cube2x2Cover" component={Cube2x2Cover} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="FunEconomics01Zh" component={FunEconomics01Video} durationInFrames={18000} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"zh"}} calculateMetadata={calculateEconMetadata} />
      <Composition id="FunEconomics01En" component={FunEconomics01Video} durationInFrames={18000} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"en"}} calculateMetadata={calculateEconMetadata} />
      <Composition id="FunEconomics01CoverZh" component={FunEconomics01Cover} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="FunEconomics01CoverEn" component={FunEconomics01CoverEn} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="FunEconomics01ExtraZh" component={FunEconomics01ExtraVideo} durationInFrames={3600} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"zh"}} calculateMetadata={calculateExtraMetadata} />
      <Composition id="FunEconomics01ExtraEn" component={FunEconomics01ExtraVideo} durationInFrames={3600} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"en"}} calculateMetadata={calculateExtraMetadata} />
      <Composition id="FunEconomics01ExtraCoverZh" component={FunEconomics01ExtraCover} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="FunEconomics01ExtraCoverEn" component={FunEconomics01ExtraCoverEn} durationInFrames={1} fps={30} width={1920} height={1080} />
      {/* Education Economics 2 (folders keep the fun-economics-02 name): one film per language, same shot list. */}
      <Composition id="FunEconomics02Zh" component={FunEconomics02Video} durationInFrames={18000} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"zh"}} calculateMetadata={calculateFe02Metadata} />
      <Composition id="FunEconomics02En" component={FunEconomics02Video} durationInFrames={18000} fps={30} width={1920} height={1080} defaultProps={{tl:null,lang:"en"}} calculateMetadata={calculateFe02Metadata} />
      <Composition id="FunEconomics02Cover" component={FunEconomics02Cover} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="FunEconomics02CoverEn" component={FunEconomics02CoverEn} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="NewsEducation01" component={NewsEducation01Video} durationInFrames={18000} fps={30} width={1920} height={1080} defaultProps={{tl:null,maps:null}} calculateMetadata={calculateNe01Metadata} />
      <Composition id="NewsEducation01Cover" component={NewsEducation01Cover} durationInFrames={1} fps={30} width={1280} height={720} />
      <Composition id="NewsEducation01CoverEn" component={NewsEducation01CoverEn} durationInFrames={1} fps={30} width={1280} height={720} />
      {/* 好奇新世界 / Curious Worlds (WEEKLY-VIDEO.md): a Chinese film and an English film per episode, and a cover for each */}
      <Composition id="Weekly001" component={WeeklyEpisode} durationInFrames={27000} fps={30} width={1920} height={1080} defaultProps={{episode: '001', lang: 'zh' as const, tl: null}} calculateMetadata={calculateWeeklyMetadata} />
      <Composition id="Weekly001En" component={WeeklyEpisode} durationInFrames={27000} fps={30} width={1920} height={1080} defaultProps={{episode: '001', lang: 'en' as const, tl: null}} calculateMetadata={calculateWeeklyMetadata} />
      <Composition id="Weekly001Cover" component={WeeklyCover} durationInFrames={1} fps={30} width={1920} height={1080}
        defaultProps={{episode: '001', lang: 'zh' as const, zh: '一个小小的想法，\n能长成一个世界吗？', en: 'Can a small idea grow into a world?', bg: 'captures/zh/van-gogh-room.mp4', at: 47, focus: '60% 50%'}} />
      <Composition id="Weekly001CoverEn" component={WeeklyCover} durationInFrames={1} fps={30} width={1920} height={1080}
        defaultProps={{episode: '001', lang: 'en' as const, zh: '一个小小的想法，能长成一个世界吗？', en: 'Can a small idea\ngrow into a world?', bg: 'captures/zh/van-gogh-room.mp4', at: 47, focus: '60% 50%'}} />
    </>
  );
};
