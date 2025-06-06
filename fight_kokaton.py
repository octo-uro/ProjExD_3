import os
import random
import sys
import time
import pygame as pg
import math


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の個数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # こうかとんの向きを表すタプルを追加

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)  # 向きを更新
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")
        self.vx, self.vy = bird.dire  # こうかとんが向いている方向を速度ベクトルとして使用
        angle = math.degrees(math.atan2(-self.vy, self.vx))  # 角度を計算（弧度法から度数法に変換）
        self.img = pg.transform.rotozoom(self.img, angle, 1.0)  # 画像を回転
        self.rct = self.img.get_rect()
        # こうかとんの向きを考慮した初期配置
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx / 10
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy / 10

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    """
    スコアを表示するクラス
    """
    def __init__(self):
        """
        フォントの設定、スコアの初期化
        """
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)  # 青色
        self.score = 0  # スコアの初期値
        self.img = self.font.render(f"スコア: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)  # 画面左下（横100, 縦は画面下から50）

    def update(self, screen: pg.Surface):
        """
        現在のスコアを表示する
        引数 screen：画面Surface
        """
        self.img = self.font.render(f"スコア: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, bomb_rct: pg.Rect):
        """
        爆発エフェクトを初期化する
        引数 bomb_rct：爆発する爆弾のRect
        """
        # 爆発画像を読み込み、元の画像と上下左右にフリップした画像をリストに格納
        self.imgs = [
            pg.image.load("fig/explosion.gif"),
            pg.transform.flip(pg.image.load("fig/explosion.gif"), True, True)
        ]
        self.rct = self.imgs[0].get_rect()
        self.rct.center = bomb_rct.center  # 爆発位置は爆弾の中心
        self.life = 30  # 爆発の表示時間
        self.img_idx = 0  # 画像インデックス（交互に切り替えるため）

    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを更新する
        引数 screen：画面Surface
        """
        self.life -= 1  # ライフを1減らす
        if self.life > 0:
            # 爆発経過時間が残っている場合、ゆっくり画像を切り替える（10フレームに1回切り替え）
            self.img_idx = int(self.life // 10 % 2)
            screen.blit(self.imgs[self.img_idx], self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    beams = []
    bird = Bird((300, 200))
    
    # NUM_OF_BOMBS個の爆弾インスタンスをリストで生成（内包表記）
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    
    # スコアインスタンスの生成
    score = Score()
    
    # 爆発エフェクトインスタンス用の空リストを作成
    explosions = []
    
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beams.append(Beam(bird))            
        screen.blit(bg_img, [0, 0])
        
        # こうかとんと爆弾の衝突判定
        for i, bomb in enumerate(bombs):
            if bomb is not None:
                if bird.rct.colliderect(bomb.rct):
                    # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                    bird.change_img(8, screen)
                    font = pg.font.Font(None, 80)
                    txt = font.render("GAME OVER", True, (255, 0, 0))
                    screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                    pg.display.update()
                    time.sleep(1)
                    return
        
        # ビームと爆弾の衝突判定
        
        for i, bomb in enumerate(bombs):
            for j, beam in enumerate(beams):
                if beam is not None and bomb is not None:
                    # ビームと爆弾が衝突した場合   
                    if beam.rct.colliderect(bomb.rct):
                        bird.change_img(6, screen)
                        # 爆発エフェクトを生成
                        explosions.append(Explosion(bomb.rct))
                        bombs[i] = None
                        beams[j] = None
                        score.score += 1 # スコアを1点加算
                        break
        
        # 爆弾リストの更新: Noneでない要素だけのリストにする
        bombs = [bomb for bomb in bombs if bomb is not None]
        # ビームリストの更新: Noneでない要素だけのリストにする
        beams = [beam for beam in beams if beam is not None]
        # 画面外に出たビームをリストから削除
        beams = [beam for beam in beams if check_bound(beam.rct) == (True, True)]
        # 爆発エフェクトのライフが残っている要素だけのリストにする
        explosions = [explosion for explosion in explosions if explosion.life > 0]
        
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        # ビーム描画更新
        for beam in beams:
            beam.update(screen)
            
        # 爆弾描画更新
        for bomb in bombs:
            bomb.update(screen)
        
        # 爆発エフェクト描画更新
        for explosion in explosions:
            explosion.update(screen)
        
        # スコアの更新と描画
        score.update(screen)
            
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
