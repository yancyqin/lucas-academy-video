# 计算机怎么算 1+1=？ 文字稿 v2（2026-10-06 · 待你核对）

按你挪过的顺序理顺了衔接，共 96 句。新编号在前，括号里是原编号（对照 storyboard 截图用）。每句下面是英文。
**加粗**的词配音时会读重一点。直接在这份里改就行，改完告诉我。

## 00 · 开场：计算机的图像能无限放大吗？

**00-01**（it00-01）计算机怎么算 1+1？在回答这个问题之前，我们先问另一个问题。
> How does a computer add 1 + 1? Before we answer that, let's ask a different question first.

**00-02**（it00-02）计算机里的图像，能不能**无限**放大、无限缩小？
> Can a picture inside a computer be zoomed in, and out, **forever**?

**00-03**（it00-03）看这段画面。放大，再放大，再放大……每一层里面，都还有新的东西。
> Watch this. Zoom in, zoom in again, and again... and inside every layer, there is something new.

**00-04**（it00-04）看起来，计算机的图像好像真的可以无限放大。
> It looks as if a computer picture really can be zoomed in forever.

**00-05**（it00-05）真的是这样吗？先把这个问题放一放。
> Is that really so? Let's put that question aside for a moment.

## 01 · 引子：计算机怎么算 1+1？

**01-01**（it01-01）我们先回到最开始的问题：计算机怎么算 **1+1**？
> Let's go back to the first question: how does a computer add **1 + 1**?

**01-02**（it01-02）你可能会说，这还用算？当然是 2 呀！
> You might say: that's easy. It's 2.

**01-03**（it01-03）可是你打开一台计算机，往里面看：**没有**数字。没有 1，也没有 2。
> But open a computer and look inside. **No numbers**. No 1, and no 2.

**01-04**（it01-04）只有一块块电路，密密麻麻的线。线的尽头，是一个个小得看不见的**开关**。开，或者关。
> Only circuits, and lines packed close together. At the end of every line, a **switch** too small to see. On, or off.

**01-05**（it01-05）就靠这些开关，它算出了 1+1，也画出了刚才那段放不完的图像。
> With nothing but these switches, it adds 1 + 1, and it draws that picture that never ran out.

**01-06**（it01-06）今天我们不急着回答。先走进一个房间，慢慢看。
> Today we won't rush to answer. First, let's walk into a room and look slowly.

**01-07**（it01-07）这是 Lucas Academy 太空博物馆里的「像素科学室」。它就是为这两个问题造的。
> This is the Pixel Science Room, in the Lucas Academy space museum. It was built for exactly these two questions.

## 02 · 两个状态，一个比特

**02-01**（it02-01）先看中间这面墙。绿色的符号，像雨一样落下来。
> Start with the middle wall. Green symbols fall like rain.

**02-02**（it02-02）看，一个位置，只有两种样子：**暗**，或者**亮**。
> Look: one spot can only be two ways. **Dark**, or **bright**.

**02-03**（it02-03）我们给这两种样子起个名字，写成 **0** 和 **1**。
> We give those two ways names, and write them **0** and **1**.

**02-04**（it02-04）这样一个“二选一”，叫做一个**比特**。
> One choice between two: that is a **bit**.

**02-05**（it02-05）比特不是一张小图，也不是半个字母。它只记一件事：选了哪一个。
> A bit is not a tiny picture, or half a letter. It records just one thing: which of the two was chosen.

**02-06**（it02-06）就像家里的电灯开关：不是关，就是开。计算机里那些小开关，记的就是比特。
> Like the light switch at home: either off, or on. Those tiny switches inside a computer hold bits.

## 03 · 只用两个符号数数

**03-01**（it03-01）可是，只有 0 和 1，怎么数数呢？
> But with only 0 and 1, how do you count?

**03-02**（it03-02）我们平时有十个数字。9 再加 1，就要**进位**，写成 10。
> We usually have ten digits. Add 1 to 9, and you have to **carry**: you write 10.

**03-03**（it03-03）计算机只有两个数字。它的每一个位置，就像前面那个开关，只有开、关两种样子，只能是 0 或 1，最大就是 1。所以 1 再加 1，也要进位，写成 10，读作“一零”，不是十哦。
> A computer has only two digits. Each place in it is like that switch: only on or off, only 0 or 1. The biggest digit is 1. So add 1 to 1, and it has to carry too: it writes 10, read “one, zero”. Not ten!

**03-04**（it03-04）看墙上：0000 是 0。
> Watch the wall: 0000 is 0.

**03-05**（it03-04）0001 是 1。
> 0001 is 1.

**03-06**（it03-04）再加 1，要进位，就是 0010，也就是 2。
> Add 1, carry, and it's 0010. That's 2.

**03-07**（it03-04）0010 再加 1，就是 0011，也就是 3。
> 0010 plus 1 is 0011. That's 3.

**03-08**（it03-04）再加 1，连着进两位，就是 0100，也就是 4。
> Add 1 more, carry twice, and it's 0100. That's 4.

## 04 · 开关怎么相加：1+1=10

**04-01**（it06-07）那开关自己，是怎么算出 1 加 1 的呢？
> So how do the switches themselves add 1 + 1?

**04-02**（it07-01）我们在房间的玻璃上画一画。两个开关，两盏灯。
> Let's draw it on the room's glass. Two switches, two lamps.

**04-03**（it07-02）第一盏灯叫“**和**”：两个开关里**只有一个**开着，它亮。
> The first lamp is called **SUM**. It lights when **exactly one** of the switches is on.

**04-04**（it07-03）第二盏灯叫“**进位**”：两个开关**都**开着，它亮。
> The second lamp is called **CARRY**. It lights when **both** switches are on.

**04-05**（it07-04）试试看。关、关：两盏灯都不亮，0 加 0 等于 0。
> Let's try. Off, off: no lamp lights. 0 plus 0 is 0.

**04-06**（it07-05）开、关：和灯亮了，0 加 1 等于 1。
> On, off: the SUM lamp lights. 0 plus 1 is 1.

**04-07**（it07-06）开、开：和灯灭，进位灯亮。把两盏灯连起来读，进位是 1，和是 0，就是 **10**。
> On, on: SUM goes dark, CARRY lights. Read the two lamps together, CARRY then SUM: 1, 0. That's **10**.

**04-08**（it03-06）所以在计算机里，1+1 不写成 2，而是写成 **10**，读作“一零”。
> So inside a computer, 1 + 1 is not written 2. It's written **10**: “one, zero”.

**04-09**（it03-07）就这样一直加 1，加到第 65 次，八个开关排成了 01000001，它就是 65。
> Keep adding 1, sixty-five times, and eight switches read 01000001. That is 65.

## 05 · 换一条规则，数字变字母

**05-01**（it04-01）65 有什么特别的**意思**呢？
> Does 65 **mean** anything special?

**05-02**（it04-02）数字自己，不会说自己是干什么用的，65 并没有什么特别的意思。
> A number doesn't tell you what it's for. On its own, 65 means nothing special.

**05-03**（it04-03）但是，很久以前，人们约定了一张表，叫 **ASCII**：在这张表里，65 就代表大写字母 A。
> But long ago, people agreed on a table called **ASCII**. In that table, 65 stands for the capital letter A.

**05-04**（it04-04）你看，比特一个都没变。变的是**读它的规则**。
> Look: not one bit has changed. What changed is **the rule for reading it**.

**05-05**（it04-05）再来几组比特，按同一张表读：H、E、L、L、O。信息第一次**开口说话**了。
> A few more groups of bits, read by the same table: H, E, L, L, O. For the first time, the information **speaks**.

## 06 · 像素：最小单元，排列才是图画

**06-01**（it05-01）很多 0 和 1 在一起，除了字母，还能变成什么？换一面墙看看。这面墙上的小零件叫**像素**：屏幕上的一个点，也是屏幕上**最小**的一块。
> Many 0s and 1s together: besides letters, what else can they become? Let's look at another wall. Its tiny pieces are called **pixels**: one dot on a screen, and the **smallest** piece a screen has.

**06-02**（it05-02）1 个像素，2 个，3 个。36 个小方块排成八行，是一个三角形。
> One pixel, two, three. Thirty-six little squares in eight rows make a triangle.

**06-03**（it05-03）现在，2,309 个彩色的点，各飞各的。你能看出这是什么吗？
> Now 2,309 coloured dots fly around on their own. Can you tell what this is?

**06-04**（it05-04）它们落下来了，落到从一张星系照片里取出的位置上。
> They land, on spots copied from a photo of a galaxy.

**06-05**（it05-05）一个点，几乎说明不了什么。真正装着图画的，是它们的**排列**。
> One dot tells you almost nothing. What holds the picture is the **arrangement**.

**06-06**（it05-06）位置一放开，图画就散了。
> Let the positions go, and the picture falls apart.

**06-07**（it05-07）那颜色呢？回到比特的墙，换一条规则来读：三组比特，分别是红、绿、蓝，三个数合成一个颜色。
> And colour? Back on the bits wall, read with another rule: three groups of bits are red, green and blue. Three numbers make one colour.

**06-08**（it05-08）很多这样的小方块，放对位置，就是一幅画。**比特变颜色，像素变图画。**
> Many little squares like that, in the right places, make a picture. **Bits to colour, pixels to image.**

**06-09**（it05-09）再看：1,260 个像素，挤在一起是一个**点**；排成一行是一条**线**；铺开，是一个**面**。
> Look again: 1,260 pixels crowded together are a **point**. In a row, a **line**. Spread out, a **plane**.

**06-10**（it05-10）一个立方体慢慢变圆，变成一个球；三角形散开，又聚成**圣母与圣子**。
> A cube slowly rounds into a ball; triangles scatter, and gather again as **Madonna and Child**.

**06-11**（it05-11）什么都没有加。同样的像素，换一条规则，就换一个形状。
> Nothing was added. The same pixels, under a different rule, make a different shape.

## 07 · 回答第一个问题：有最小单元，无限是算出来的

**07-01**（it06-01）现在，可以回答开头的问题了。计算机的图像，能不能无限放大？
> Now we can answer the question from the start. Can a computer picture be zoomed in forever?

**07-02**（it06-02）把墙上这幅像素图放大，再放大。看，变成了一块一块的方格。
> Zoom into this pixel picture on the wall. Closer, and closer. Look: it turns into little squares.

**07-03**（it06-03）屏幕上的图，是**有最小单元**的。放到底，就是像素。
> A picture on a screen has a **smallest unit**. Zoom all the way in, and you reach the pixel.

**07-04**（it06-04）可是开头那段画面，为什么放多大都有新东西？
> Then why did that picture at the start keep showing new things, however far we zoomed?

**07-05**（it06-05）因为那张图不是存好的。每放大一次，程序就按一条规则，**重新算**出一张新的图。
> Because that picture was never stored. Each time you zoom, the program follows a rule and **computes** a brand-new picture.

**07-06**（it06-06）新的图，还是有限的像素。“无限”的感觉，是算出来的。
> The new picture is still a finite set of pixels. The feeling of “infinite” is computed.

**07-07**（it07-07）怎么算的？没有魔法，也没有谁躲在里面算。还是那个 1+1：电按规则，流过开关。
> How is it computed? No magic, and nobody hiding inside. It's still that 1 + 1: electricity, following a rule, through switches.

**07-08**（it07-08）要算更大的数，就多排几组开关；要算乘法，就把加法做很多次。
> For bigger numbers, line up more groups of switches. For multiplication, do addition many times over.

**07-09**（it07-09）一台计算机里有**几十亿**个这样的开关，一秒钟开关几十亿次。
> One computer holds **billions** of switches like these, flipping billions of times a second.

**07-10**（it07-10）刚才那幅放不完的图，每一个像素的颜色，都是这样一次次 1+1 算出来的。
> That picture that never ran out: the colour of every pixel was computed this way, one 1 + 1 at a time.

**07-11**（it07-11）算出来的数，除了颜色，还能变成什么？
> Besides a colour, what else can a computed number become?

## 08 · 同一串 0 和 1，五种意思

**08-01**（it08-01）声音是一串数，一个接一个，画出一条起伏的波。
> Sound is a string of numbers, one after another, drawing a wave that rises and falls.

**08-02**（it08-02）动作呢？位置是数，时间是数。一个点按这些数走，就动起来了。
> Motion? A position is a number; a moment in time is a number. A dot follows those numbers, and it moves.

**08-03**（it08-03）现在，再看这一串：01000001。还是它。
> Now look at this string again: 01000001. The same one.

**08-04**（it08-04）它可以是 **65**，可以是 **A**，可以是一个像素，一小段声音，或者一个动作。
> It can be **65**. It can be **A**. It can be a pixel, a slice of sound, or a move.

**08-05**（it08-05）同一串 0 和 1，**五种意思**。它一次都没变，变的只是规则。
> One string of 0s and 1s, **five meanings**. It never changed once. Only the rule did.

**08-06**（it08-06）用一句话说：规则给比特意义。两个符号，许多世界。
> The wall says it: a code gives bits meaning. Two symbols, many worlds.

## 09 · 游戏怎么做：规则加数字

**09-01**（it09-01）那一张会动的图，比如游戏，是怎么做出来的？先看贪吃蛇。
> So how is a moving picture, like a game, made? The third wall. First, Snake.

**09-02**（it09-02）每一步，蛇头前进一格，身子跟上。棋盘上一百多个格子，其实只有**几个数**在变。
> Each turn, the head moves one square and the body follows. Over a hundred squares on the board, and only **a few numbers** change.

**09-03**（it09-03）下一帧，不是画好存着的。是程序按规则，从这几个数**算**出来的。
> The next frame is not drawn and stored. The program **computes** it from those few numbers, by the rules.

**09-04**（it09-04）三条蛇的竞技场也一样：规则多了几条，要记的数多了几个，画面就复杂了。
> The arena with three snakes works the same way: a few more rules, a few more numbers to keep, and the picture gets complicated.

**09-05**（it09-05）那你最喜欢的游戏是什么？不管是哪一个，它都是这样做出来的：用规则去读很多很多很多数字。
> The wall ends by asking: what is your favourite game? Whichever it is, it was made the same way: rules reading lots and lots and lots of numbers.

**09-06**（it09-06）开头那段放大，也是这样做的。它的规则，只有一行公式。
> The zoom at the start was made the same way. Its rule is a single line of formula.

**09-07**（it09-07）每一个像素，把自己的位置代进公式，算几百次，就得到自己的颜色。
> Every pixel puts its own position into the formula, runs it a few hundred times, and gets its own colour.

**09-08**（it09-08）放大，就是换几个数，再算一遍。所以它永远有新东西。
> Zooming in just means changing a few numbers and computing again. That is why there is always something new.

**09-09**（it09-09）**无限不在图里，在规则里。**图，每次都是有限的。
> **The infinity is not in the picture. It is in the rule.** The picture is finite every time.

## 10 · 香农的尺子：信息 = 要问几个问题

**10-01**（it10-01）1948 年，一个叫**克劳德·香农**的科学家，想出了一把量信息的尺子：要知道一件事，得**问几个问题**。
> In 1948, a scientist named **Claude Shannon** found a ruler for measuring information: to learn something, **how many questions** do you have to ask?

**10-02**（it10-02）玩个游戏。我心里想了 1 到 8 里的一个数，你只能问“是不是”的问题。
> Let's play. I'm thinking of a number from 1 to 8, and you may only ask yes-or-no questions.

**10-03**（it10-03）“比 4 大吗？”“比 6 大吗？”“是 7 吗？”三个问题，一定能猜到。
> “Is it bigger than 4?” “Bigger than 6?” “Is it 7?” Three questions, and you're sure to get it.

**10-04**（it10-04）香农说：这个数里装的信息，就是 3 个问题，叫 **3 比特**。一个问题，就是一个比特。
> Shannon said: the information in that number is 3 questions. Call it **3 bits**. One question is one bit.

**10-05**（it10-05）要是答案你早就知道呢？比如一枚两面都是正面的硬币，抛出去不用猜，一个问题都不用问，信息就是 0。**能猜到的事，不算信息。**
> And if you already know the answer? Toss a coin with heads on both sides: no need to guess, no question to ask. The information is 0. **What you can guess doesn't count.**

**10-06**（it10-06）回到贪吃蛇。要知道下一帧，我只用问一件事：玩家按了哪个方向？四个方向，最多两个问题。
> Back to Snake. To know the next frame, I only have to ask one thing: which way did the player press? Four directions: two questions at most.

**10-07**（it10-07）剩下的格子，规则替我们算出来，不用问。所以棋盘再大，一步也最多 **2 比特**。
> Every other square, the rules work out for us. No questions needed. So however big the board, one step is at most **2 bits**.

**10-08**（it10-08）五子棋每一步，一百多个点，“落在哪儿？”大约七个问题。55 步，几百个问题。一整盘棋，就装在这几百个比特里。
> In Gomoku, each move has over a hundred spots to choose from. “Where did it go?” About seven questions. 55 moves: a few hundred questions. A whole game fits in those few hundred bits.

**10-09**（it10-09）开头那段放大的视频呢？要是你也知道那条公式，我只要告诉你几个数：从哪儿开始，放多快，放多久。一百来个问题，就是一整段视频。
> And that zoom from the start? If you know the formula too, I only have to tell you a few numbers: where to start, how fast, how long. A hundred or so questions, and you have the whole clip.

**10-10**（it10-10）房间中央这座耶稣降生像不一样：它是**量**出来的。两万个三角形，每一个在哪儿都得问，几百万个问题。没有公式能替你省掉。
> The Nativity in the middle of the room is different: it was **measured**. Twenty thousand triangles, and you have to ask where every one of them is. Millions of questions. No formula can save you those.

**10-11**（it10-11）这就是香农的尺子：信息不是说了多少，是你**还得问多少**。不管装的是字、图、声音还是棋，都用这一把尺子量。
> That is Shannon's ruler. Information isn't how much was said. It's how much you **still have to ask**. Words, pictures, sound or a game: all measured with the same ruler.

## 11 · 回到两个问题

**11-01**（it11-01）现在，回到我们的两个问题。计算机怎么算 1+1？它用两个开关，算出了 10。
> Now, back to our two questions. How does a computer add 1 + 1? With two switches, it got 10.

**11-02**（it11-02）计算机的图像能无限放大吗？不能。图有最小单元。无限的感觉，来自一条规则，和几十亿次 1+1。
> Can a computer picture be zoomed in forever? No. A picture has a smallest unit. The feeling of infinity comes from one rule, and billions of 1 + 1s.

**11-03**（it11-03）你看这整个房间：图画、字母、声音、游戏、一个立体的形状……
> But look at this whole room: pictures, letters, sound, games, a solid shape...

**11-04**（it11-04）全都是那**同一种开关**，排好，连上，再按规则一起读。
> All of it is **the same kind of switch**, arranged, connected, and read together by a rule.

**11-05**（it11-05）最后这一句是写给你的：像素放对了位置，就变成字母——于是，也变成别的东西。
> The last line on the wall is written for you: pixels in the right place become letters, and so form other things.

**11-06**（it11-06）从此以后，再复杂的图像，你也知道它背后是什么了：许多小小的像素，按规则排在一起。
> From now on, however complex a picture is, you know what's behind it: many tiny pixels, arranged by a rule.

**11-07**（it11-07）下一次，我们接着香农的问题往下走。
> Next time, we'll follow Shannon's question a little further.

**11-08**（it11-08）这个房间就在 Lucas Academy 的太空博物馆里。你也可以自己走进来，按 R，慢慢看。
> This room is in the Lucas Academy space museum. You can walk in yourself, press R, and look slowly.

---

## 镜头调整清单（确认后照这个改）

你在分镜里改的：

1. **00-05** 分形不定格，从 00-02 一直放大到这句说完；卡片改成「真的是这样吗？」。
2. **03-04 到 03-08**（原 it03-04）墙上 0000 → 0、0001 → 1……一行行出现，每一行出现的时候正好说到它。为了对得准，这句拆成了五小句。
3. 卡片上的「电脑」全部改「计算机」：00-02 的问题卡、01-01 的小字、01-03 的提示条、03-02 进位卡右栏「计算机的数」、07-01 的问题卡。
4. 片名卡、结束卡、封面、YouTube 标题改成「计算机怎么算 1+1=？」。

跟着台词改动走的：

5. **04 段**（加法器）整段挪到数数后面，房间玻璃格点和加法器卡跟着走；大字卡「1 + 1 = 10」放在 04-08。
6. **04-09** 画面：比特墙 01000001 → 65（原 it03-07 的画面不变）。
7. 删掉的三句，画面一起去掉：原 it03-05 的提示条、原 it04-06 的展签页、原 it09-10 的「算过头碎成色块」分形和提示条。
8. **07-07 到 07-10**（加法器后半：电流流动、四组开关接成一排、满屏开关、每个像素几百次 z² + c）留在原位置，接在回答第一个问题之后。
9. **07-11** 卡片改成「算出来的数，除了颜色，还能变成什么？」。
10. **10-05** 香农尺子上的 0 改成「两面都是正面的硬币」，1 改成「抛一次普通硬币」。
11. **11-06** 卡片改成新台词（原来卡上是墙上那句「不要被复杂的图像吓到」）。
12. **11-08** 「按 E」改成「按 R」：在博物馆里 R 才是打开展签，E 会打开房间编辑器。结束卡上本来就写的是 R。
