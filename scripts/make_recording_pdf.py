"""Build the printable recording guide handed to a singer before a session.

    python scripts/make_recording_pdf.py [en|zh] [out.pdf]

Both languages come out of the one set of (en, zh) pairs below, so the two sheets
cannot drift apart when a number changes.

Kept as a script rather than a hand-made PDF so the figures stay tied to what was
actually measured on this project (see voice-cover/VOICE-GUIDE.md).

Glyph traps: reportlab's built-in Latin fonts draw check marks, arrows and >= as
solid black boxes, so none appear here. Chinese needs a real CJK face -- the
built-in STSong-Light CID font has no bold, and this sheet leans on bold, so it
loads Songti SC Regular and Bold out of the macOS TTC instead.
"""
import sys, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)

LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
OUT  = sys.argv[2] if len(sys.argv) > 2 else (
        'voice-cover/RECORDING-GUIDE.pdf' if LANG == 'en' else 'voice-cover/RECORDING-GUIDE-zh.pdf')

SONGTI = '/System/Library/Fonts/Supplemental/Songti.ttc'
if LANG == 'zh':
    if not os.path.exists(SONGTI):
        sys.exit(f'need a CJK font: {SONGTI} not found')
    pdfmetrics.registerFont(TTFont('CJK',      SONGTI, subfontIndex=6))   # Songti SC Regular
    pdfmetrics.registerFont(TTFont('CJK-Bold', SONGTI, subfontIndex=1))   # Songti SC Bold
    pdfmetrics.registerFontFamily('CJK', normal='CJK', bold='CJK-Bold',
                                  italic='CJK', boldItalic='CJK-Bold')
    FN, FB, FI = 'CJK', 'CJK-Bold', 'CJK'
else:
    FN, FB, FI = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'

INK   = colors.HexColor('#1a1a1a'); MUTED = colors.HexColor('#666666')
GOOD  = colors.HexColor('#1c6b3f'); BAD   = colors.HexColor('#a32020')
RULE  = colors.HexColor('#cccccc'); BAND  = colors.HexColor('#f2f2f2')

ss = getSampleStyleSheet()
S = {
 'title':  ParagraphStyle('t', parent=ss['Title'], fontName=FB, fontSize=19,
                          leading=23, textColor=INK, alignment=TA_LEFT, spaceAfter=2),
 'sub':    ParagraphStyle('s', parent=ss['Normal'], fontName=FN, fontSize=9.5,
                          leading=12.6, textColor=MUTED, spaceAfter=8),
 'h':      ParagraphStyle('h', parent=ss['Heading2'], fontName=FB, fontSize=12.5,
                          leading=14.5, textColor=INK, spaceBefore=9.5, spaceAfter=4),
 'body':   ParagraphStyle('b', parent=ss['Normal'], fontName=FN, fontSize=9.6,
                          leading=12.7, textColor=INK, spaceAfter=4),
 'bullet': ParagraphStyle('bu', parent=ss['Normal'], fontName=FN, fontSize=9.6,
                          leading=12.6, textColor=INK, leftIndent=11,
                          bulletIndent=2, spaceAfter=2),
 'note':   ParagraphStyle('n', parent=ss['Normal'], fontName=FI, fontSize=9,
                          leading=12.5, textColor=MUTED, spaceAfter=5),
 'cell':   ParagraphStyle('c', parent=ss['Normal'], fontName=FN, fontSize=9,
                          leading=12, textColor=INK),
 'cellb':  ParagraphStyle('cb', parent=ss['Normal'], fontName=FB, fontSize=9,
                          leading=12, textColor=INK),
}
def _zh_punct(s):
    """Fullwidth the , : ; that follow a Chinese character.

    The source keeps ASCII punctuation so the strings stay easy to edit; halfwidth
    commas sitting next to a fullwidth period look wrong on the page. Anchoring on
    a preceding CJK character leaves markup, numbers and note names untouched.
    """
    import re
    for a, b in ((',', '，'), (':', '：'), (';', '；')):
        s = re.sub(r'(?<=[一-鿿])' + re.escape(a), b, s)
    return s

def T(v):
    if not isinstance(v, tuple): return v
    return v[0] if LANG == 'en' else _zh_punct(v[1])
P  = lambda t, s='body': Paragraph(T(t), S[s])
def BU(t): return Paragraph(T(t), S['bullet'], bulletText='•')
def rule(): return HRFlowable(width='100%', thickness=0.6, color=RULE,
                              spaceBefore=6, spaceAfter=8)
def table(rows, widths, align=None):
    data = [[Paragraph(T(c), S['cellb' if r == 0 else 'cell']) for c in row]
            for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign='LEFT', repeatRows=1)
    st = [('VALIGN', (0,0), (-1,-1), 'TOP'),
          ('LINEBELOW', (0,0), (-1,-2), 0.4, RULE),
          ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
          ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
          ('BACKGROUND', (0,0), (-1,0), BAND),
          ('LINEBELOW', (0,0), (-1,0), 0.8, MUTED)]
    if align: st += align
    t.setStyle(TableStyle(st)); return t

story = []; A = story.append

A(P(('Recording a Voice for Conversion', '声音转换录音指南'), 'title'))
A(P(('Session guide. The recording is the ceiling on everything downstream '
     '&mdash; no amount of processing recovers detail the microphone never captured.',
     '录音是整条链路的上限。麦克风没有录到的细节,后期再怎么处理也变不出来。'), 'sub'))
A(rule())

A(P(('Why this sheet exists', '为什么要有这张纸'), 'h'))
A(P(('The voice model on this project reproduced the singer accurately. It was '
     'measured against his own recordings and tracked them within a few dB in '
     'every frequency band. The problem was that the recordings themselves were '
     'far darker than a studio vocal:',
     '这个项目训练出来的模型还原度没有问题:把它的输出和歌手自己的录音逐频段对比,'
     '每个频段都在几个 dB 以内。问题出在录音本身 —— 它比录音棚人声暗得多:'), 'body'))
A(Spacer(1, 3))
A(table([
    [('Frequency band', '频段'), ('Studio vocal', '录音棚人声'),
     ('Phone take', '手机录音'), ('Shortfall', '差距')],
    [('2&ndash;4 kHz &mdash; presence, the "front" of a voice',
      '2&ndash;4 kHz — 存在感,一个嗓子顶不顶得出来'),
     '-9.9 dB', '-26.1 dB', '<font color="#a32020"><b>16 dB</b></font>'],
    [('8&ndash;11 kHz &mdash; air, the sheen on top',
      '8&ndash;11 kHz — 空气感,高频的那层光泽'),
     '-26.4 dB', '-55.0 dB', '<font color="#a32020"><b>28 dB</b></font>'],
], [78*mm, 26*mm, 24*mm, 24*mm]))
A(Spacer(1, 4))
A(P(('The model learned that dullness faithfully, because that is what it was '
     'given. Mix processing later recovered the presence band, but the air above '
     '8 kHz had to be synthesised &mdash; there was nothing real up there to lift. '
     'A better recording fixes at the source what everything else can only imitate.',
     '模型忠实地学会了这种沉闷,因为给它的就是这个。后期混音把存在感那一段救了回来,'
     '但 8 kHz 以上的空气感只能靠激励器合成 —— 那里本来就没有真东西可以提。'
     '换一个更好的录音,是从源头解决其他环节只能模仿的问题。'), 'body'))

A(P(('The room: dry, not resonant', '房间:要闷,不要空'), 'h'))
A(P(('This is the one place instinct points the wrong way. A stairwell, a bathroom '
     'or a church makes singing feel and sound wonderful in the moment &mdash; and '
     'each is close to the worst possible choice for this purpose.',
     '这是唯一一个直觉会指反方向的地方。楼梯间、卫生间、教堂,当场唱起来又爽又好听 ——'
     '而对训练素材来说,这几个几乎是最差的选择。'), 'body'))
A(Spacer(1, 2))
A(BU(('Reverb is recorded <b>into</b> the voice. The model cannot tell a room '
      'from a throat, so it learns the room as part of the timbre and then carries '
      'it into every song afterwards.',
      '混响是被录<b>进</b>声音里的。模型分不清房间和嗓子,'
      '它会把房间当成音色的一部分学进去,然后带进以后每一首歌。')))
A(BU(('It cannot be removed later. De-reverb processing is lossy and audibly '
      'damages the voice.',
      '事后去不掉。去混响算法有损,会明显伤害人声。')))
A(BU(('The mix adds its own reverb at the end. A reverberant source gets it '
      'twice and turns to mush.',
      '混音阶段还会再加一层混响。本来就湿的素材会叠两次,糊成一团。')))
A(BU(('Small hard rooms &mdash; bathroom, stairwell &mdash; are the worst of all. '
      'Their strong early reflections comb-filter the direct sound, which eats '
      'exactly the high frequencies this recording is trying to gain.',
      '小而硬的房间(卫生间、楼梯间)是最糟的。强烈的早期反射会对直达声形成梳状滤波,'
      '吃掉的恰恰是这次录音想要争取的高频。')))
A(Spacer(1, 5))
A(table([
    [('Record here', '在这里录'), ('Not here', '不要在这里录')],
    [('A closet, standing among hanging clothes', '衣柜里,站在挂着的衣服中间'),
     ('Bathroom or shower room', '卫生间、淋浴间')],
    [('A bedroom with a rug, curtains and a bed', '有地毯、窗帘和床的卧室'),
     ('Stairwell', '楼梯间')],
    [('Under a thick blanket draped over you and the mic', '把厚毯子连人带麦一起蒙住'),
     ('Church or hall', '教堂、礼堂')],
    [('A parked car, engine off', '停着的车里,熄火'),
     ('Any large empty room', '任何空旷的大房间')],
], [78*mm, 74*mm],
   align=[('TEXTCOLOR', (0,1), (0,-1), GOOD), ('TEXTCOLOR', (1,1), (1,-1), BAD)]))
A(Spacer(1, 5))
A(P(('<b>The clap test.</b> Stand where you plan to sing and clap once, hard. If '
     'you hear any ring or tail after the clap, the room is too live &mdash; add '
     'soft material or move. A good space sounds slightly dead and unflattering.',
     '<b>拍手测试。</b>站在准备唱的位置,用力拍一次手。如果听得到任何拖尾或回响,'
     '房间就太活了 —— 加软性材料,或者换个地方。'
     '好的录音空间听起来是有点发死、不好听的。'), 'body'))
A(P(('The instinct is not worthless: those spaces are usually quiet, and they '
     'make people sing with more confidence. Warm up in the stairwell if it helps. '
     'Then record somewhere dull.',
     '这个直觉不是没道理:那些地方通常很安静,而且让人唱得更放得开。'
     '想在楼梯间开嗓完全可以,然后回到闷的地方录。'), 'note'))

A(P(('The microphone', '麦克风'), 'h'))
A(BU(("<b>Any real microphone beats a phone held at arm's length.</b> A "
      'large-diaphragm cardioid condenser is ideal; a handheld dynamic '
      '(SM58 type) is a fine second choice and more forgiving in a live room.',
      '<b>任何一支真正的麦克风都好过一臂之外的手机。</b>大振膜心形电容麦最理想;'
      '手持动圈(SM58 那一类)是很好的第二选择,而且对房间更宽容。')))
A(BU(('<b>Distance: 15&ndash;20 cm</b>, and keep it identical across every take. '
      'Closer gets boomy, further picks up the room and loses top end.',
      '<b>距离 15—20 cm</b>,而且每一条都保持一致。太近发闷发轰,'
      '太远会收进房间声、丢掉高频。')))
A(BU(('<b>Point your mouth straight at the capsule.</b> High frequencies are '
      'directional and fall away fast off-axis. Singing past the side of a mic is '
      'a common cause of a dull recording, and likely part of the 28 dB shortfall '
      'measured above.',
      '<b>嘴要正对着拾音头。</b>高频有很强的指向性,偏轴衰减极快。'
      '对着麦克风侧面唱是录音发闷最常见的原因之一,'
      '很可能就是上面那 28 dB 差距的一部分来源。')))
A(BU(('<b>Use a pop filter</b>, or stretch a sock over the mic, and aim slightly '
      'past the capsule so plosives do not thump it.',
      '<b>用防喷罩</b>,或者套一只袜子在麦上,并让气流稍微擦过拾音头旁边,'
      '避免爆破音直接喷上去。')))
A(BU(('<b>Same mic, same distance, same room for every take.</b> Mixed conditions '
      "average out into a timbre that is nobody's.",
      '<b>每一条都用同一支麦、同样距离、同一个房间。</b>条件混杂,'
      '平均出来的会是一个谁都不像的音色。')))

A(P(('Recorder settings', '录音设置'), 'h'))
A(table([
    [('Setting', '项目'), ('Value', '设成'), ('Why', '为什么')],
    [('Sample rate', '采样率'), '48 kHz',
     ('One earlier take arrived at 16 kHz, which has no content at all above '
      '8 kHz. It could not be used and was dropped.',
      '之前有一条是 16 kHz 录的,8 kHz 以上完全没有内容,只能整条弃用。')],
    [('Bit depth / format', '位深 / 格式'),
     ("24-bit WAV, or the app's lossless option", '24-bit WAV,或 app 里的无损选项'),
     ('Compression artefacts get learned like anything else.',
      '压缩失真也会被一并学进模型。')],
    [('Noise suppression / voice isolation', '降噪 / 人声隔离'), ('OFF', '关'),
     ('It removes breath and high detail, which is precisely what is wanted.',
      '它会削掉气息和高频细节,而那正是我们要的东西。')],
    [('EQ, compression, normalise, presets', 'EQ、压缩、标准化、预设'), ('OFF', '全关'),
     ('Hand over the raw file.', '交原始文件。')],
    [('Level', '电平'), ('Peaks around -6 to -12 dBFS', '峰值在 -6 到 -12 dBFS'),
     ('Never let it clip. Clipping is unrecoverable.', '绝对不能削顶,削了救不回来。')],
], [40*mm, 42*mm, 70*mm]))

A(P(('Using the guide track', '怎么用引导音轨'), 'h'))
A(P(('<b>Wear headphones. This is not optional.</b> If the guide tone plays out '
     'of a speaker it is recorded along with the voice and becomes part of what '
     'the model learns.',
     '<b>必须戴耳机,没有例外。</b>引导音如果从音箱放出来,会连人声一起被录进去,'
     '然后变成模型学到的东西的一部分。'), 'body'))
A(Spacer(1, 2))
A(BU(('The track walks up one semitone at a time, so you are never asked to jump '
      'to a note out of nowhere. On a previous session a singer followed a guide '
      'that jumped straight to the target and sang the whole run <b>a perfect '
      'octave too low</b> without noticing &mdash; it felt right, because the '
      'note names matched. Walking up in steps prevents that.',
      '音轨是一个半音一个半音往上走的,不会突然让你跳到一个没有铺垫的音上。'
      '之前有一次,引导音直接跳到目标音,歌手整段<b>低了一个八度</b>还完全没察觉 ——'
      '因为音名是对的,感觉就是对的。级进可以从根本上避免这件事。')))
A(BU(('<b>Three passes through the whole range.</b> Sing "ah" on the first pass, '
      '"ee" on the second, "oo" on the third.',
      '<b>整个音域走三遍。</b>第一遍唱 ah,第二遍 ee,第三遍 oo。')))
A(BU(('Hold each note for as long as the tone lasts, roughly three and a half '
      'seconds. Land on the pitch rather than sliding up into it.',
      '每个音跟着引导音唱满,大约三秒半。直接落在音上,不要滑音蹭上去。')))
A(BU(('<b>A short high pip marks every C</b>, so you can tell where you are '
      'without counting.',
      '<b>每个 C 前面有一声短促的高音提示</b>,不用数也知道唱到哪了。')))
A(BU(('<b>When it climbs past your range, or drops below it, just stay silent.</b> '
      'Let the track run. Silence costs nothing; a strained squeak teaches the '
      'model a voice you do not have.',
      '<b>唱不上去、或者够不到低音,就空过去别唱。</b>让音轨继续走。'
      '静音不花任何代价;硬挤出来的声音只会教给模型一个你没有的嗓子。')))
A(BU(('One continuous recording for the whole track is fine. Do not stop and '
      'start between notes.',
      '整条音轨一次录完就行,不用在音和音之间停下来。')))

A(P(('Sing in chest or mixed voice, not breath', '用真声或混声唱,不要用气声'), 'h'))
A(P(('Breathy falsetto has almost no resonance, so the model learns nothing from '
     'it and the top of the range still comes out hollow. <b>A strained, cracking, '
     'honest note is worth more than a pretty airy one.</b> This is genuinely '
     'counter-intuitive and worth saying out loud before the take starts.',
     '气声假声几乎没有共鸣,模型从里面学不到东西,高音区照样是空的。'
     '<b>一个吃力的、破音的、真实的音,比一个漂亮空灵的音有价值得多。</b>'
     '这一点确实反直觉,开录之前值得先说清楚。'), 'body'))

A(P(('Where your range is likely to end', '你的音域大概会在哪里到头'), 'h'))
A(P(('The track runs G2 to C5, wide enough for most male voices and for the songs '
     'in hand. Expect to drop out at one end or both; that is the point of '
     'recording the whole thing once.',
     '音轨从 G2 走到 C5,对大部分男声、以及目前手上的歌来说都够宽。'
     '两端唱不到是正常的 —— 完整走一遍的意义就在于找出边界在哪。'), 'body'))
A(Spacer(1, 3))
A(table([
    [('Voice type', '声部'), ('Typical range', '常见音域'),
     ('Voice type', '声部'), ('Typical range', '常见音域')],
    [('Bass', '男低音'), 'E2 &ndash; E4', ('Alto', '女中音'), 'F3 &ndash; F5'],
    [('Baritone', '男中音'), 'G2 &ndash; G4', ('Mezzo', '次女高音'), 'A3 &ndash; A5'],
    [('Tenor', '男高音'), 'C3 &ndash; C5', ('Soprano', '女高音'), 'C4 &ndash; C6'],
], [30*mm, 42*mm, 30*mm, 42*mm]))

A(KeepTogether([
    P(('Check the first take before recording a second',
       '录第二条之前,先把第一条发来检查'), 'h'),
    P(('Send the very first file over before doing anything else. An octave error, '
       'a wrong sample rate or a live room takes seconds to spot and invalidates '
       'everything recorded after it. On this project that check would have saved '
       'an entire session.',
       '第一条录完先发过来,别的什么都先别做。八度唱错、采样率不对、房间太活,'
       '这些几秒钟就能看出来,却会让后面录的全部作废。'
       '这个项目上,这一步检查本来可以省掉一整场录音。'), 'body')]))

A(KeepTogether([
    P(('What to send back', '要交回来的东西'), 'h'),
    BU(('The raw files, unedited, in whatever format they were recorded.',
        '原始文件,不要做任何编辑,录的时候是什么格式就交什么格式。')),
    BU(('A one-line note: which microphone, which room, roughly how far away.',
        '一句话说明:用了哪支麦、在什么房间、大概多远。')),
    BU(('Ten to fifteen minutes of actual singing is plenty. Three passes of the '
        'guide gives about ten seconds per semitone, which is the target.',
        '十到十五分钟的实际发声就够了。引导音轨走三遍,每个半音约十秒,正好是目标值。'))]))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=18*mm, rightMargin=18*mm,
                        topMargin=16*mm, bottomMargin=16*mm,
                        title=T(('Recording a Voice for Conversion', '声音转换录音指南')),
                        author='Lucas Academy Video Lab')
def footer(canvas, doc_):
    canvas.saveState(); canvas.setFont(FN, 7.5); canvas.setFillColor(MUTED)
    canvas.drawString(18*mm, 10*mm, T(('Recording a Voice for Conversion', '声音转换录音指南')))
    canvas.drawRightString(A4[0]-18*mm, 10*mm, T((f'page {doc_.page}', f'第 {doc_.page} 页')))
    canvas.restoreState()
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f'  wrote {OUT}  ({LANG})')
