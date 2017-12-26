import tkinter as tk
import random

from functools import partial

from pygame import mixer

from casino import Card, Deck, Player, Dealer, assets_folder
from casino_sounds import SoundBoard


class GameScreen(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.DECK_COORDINATES = (700, 100)

        self.CARD_ORIGINAL_POSITION = 100
        self.CARD_WIDTH_OFFSET = 100

        self.PLAYER_CARD_HEIGHT = 300
        self.DEALER_CARD_HEIGHT = 100

        self.PLAYER_SCORE_TEXT_COORDS = (340, 450)
        self.PLAYER_MONEY_COORDS = (490, 450)
        self.POT_MONEY_COORDS = (500, 100)
        self.WINNER_TEXT_COORDS = (400, 250)

        self.game_state = GameState("Player")
        self.sound_board = SoundBoard()

        self.tabletop_image = tk.PhotoImage(file=assets_folder + "/tabletop.png")
        self.card_back_image = Card.get_back_file()

        self.cards_to_deal_pointer = 0
        self.frame = 0

    def setup_opening_animation(self):
        self.sound_board.shuffle_sound.play()
        self.create_image((400, 250), image=self.tabletop_image)

        self.card_back_1 = self.create_image(self.DECK_COORDINATES, image=self.card_back_image)
        self.card_back_2 = self.create_image((self.DECK_COORDINATES[0] + 20, self.DECK_COORDINATES[1]), image=self.card_back_image)

        self.back_1_movement = ([10] * 6 + [-10] * 6) * 7
        self.back_2_movement = ([-10] * 6 + [10] * 6) * 7

        self.play_card_animation()

    def play_card_animation(self):
        if self.frame < len(self.back_1_movement):
            self.move(self.card_back_1, self.back_1_movement[self.frame], 0)
            self.move(self.card_back_2, self.back_2_movement[self.frame], 0)
            self.update()
            self.frame += 1

            self.after(33, self.play_card_animation)
        else:
            self.delete(self.card_back_2)
            self.frame = 0
            self.display_table()

    def play_deal_animation(self):
        self.playing_animation = True
        self.animation_frames = 15

        self.card_back_2 = self.create_image(self.DECK_COORDINATES, image=self.card_back_image)
        self.card_back_2_pos = self.DECK_COORDINATES

        target_coords = self.cards_to_deal_positions[self.cards_to_deal_pointer]

        x_diff = self.DECK_COORDINATES[0] - target_coords[0]
        y_diff = self.DECK_COORDINATES[1] - target_coords[1]

        x_step = (x_diff / self.animation_frames) * -1
        y_step = (y_diff / self.animation_frames) * -1

        self.move_func = partial(self.move_card, item=self.card_back_2, x_dist=x_step, y_dist=y_step)
        self.move_func.__name__ = 'move_card'
        print(x_step, y_step)

        self.move_card(self.card_back_2, x_step, y_step)

    def move_card(self, item, x_dist, y_dist):
        self.move(item, x_dist, y_dist)
        self.update()
        self.frame += 1
        if self.frame < self.animation_frames:
            self.after(33, self.move_func)
        else:
            self.frame = 0
            self.delete(self.card_back_2)
            self.show_card()
            self.sound_board.place_sound.play()

            if self.cards_to_deal_pointer < (len(self.cards_to_deal_images) - 1):
                self.cards_to_deal_pointer += 1
                self.play_deal_animation()
            else:
                self.cards_to_deal_pointer = 0
                self.cards_to_deal_images = []
                self.cards_to_deal_positions = []
                self.playing_animation = False

    def show_card(self):
        self.create_image(
            self.cards_to_deal_positions[self.cards_to_deal_pointer],
            image=self.cards_to_deal_images[self.cards_to_deal_pointer]
        )

    def display_table(self, hide_dealer=True, table_state=None):
        if not table_state:
            table_state = self.game_state.get_table_state()

        player_card_images = [card.get_file() for card in table_state['player_cards']]
        dealer_card_images = [card.get_file() for card in table_state['dealer_cards']]
        if hide_dealer and not table_state['blackjack']:
            dealer_card_images[0] = Card.get_back_file()

        self.cards_to_deal_images = []
        self.cards_to_deal_positions = []

        for card_number, card_image in enumerate(player_card_images):
            image_pos = (self.CARD_ORIGINAL_POSITION + self.CARD_WIDTH_OFFSET * card_number, self.PLAYER_CARD_HEIGHT)
            self.cards_to_deal_images.append(card_image)
            self.cards_to_deal_positions.append(image_pos)

        for card_number, card_image in enumerate(dealer_card_images):
            image_pos = (self.CARD_ORIGINAL_POSITION + self.CARD_WIDTH_OFFSET * card_number, self.DEALER_CARD_HEIGHT)
            self.cards_to_deal_images.append(card_image)
            self.cards_to_deal_positions.append(image_pos)

        self.play_deal_animation()

        while self.playing_animation:
            self.master.update()

        self.create_text(self.PLAYER_SCORE_TEXT_COORDS, text=self.game_state.player_score_as_text(),
                                     font=(None, 20))
        self.create_text(self.PLAYER_MONEY_COORDS, text=self.game_state.player_money_as_text(),
                                     font=(None, 20))
        self.create_text(self.POT_MONEY_COORDS, text=self.game_state.pot_money_as_text(),
                                     font=(None, 20))

        if table_state['has_winner']:
            if table_state['has_winner'] == 'p':
                self.create_text(self.WINNER_TEXT_COORDS, text="YOU WIN!", font=(None, 50))
            elif table_state['has_winner'] == 'dp':
                self.create_text(self.WINNER_TEXT_COORDS, text="TIE!", font=(None, 50))
            else:
                self.create_text(self.WINNER_TEXT_COORDS, text="DEALER WINS!", font=(None, 50))

            self.show_next_round_options()


class GameWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blackjack")
        self.geometry("800x640")
        self.resizable(False, False)

        self.game_screen = GameScreen(self, bg="white", width=800, height=500)

        self.bottom_frame = tk.Frame(self, width=800, height=140, bg="red")
        self.bottom_frame.pack_propagate(0)

        self.hit_button = tk.Button(self.bottom_frame, text="Hit", width=25, command=self.hit)
        self.stick_button = tk.Button(self.bottom_frame, text="Stick", width=25, command=self.stick)

        self.next_round_button = tk.Button(self.bottom_frame, text="Next Round", width=25, command=self.next_round)
        self.quit_button = tk.Button(self.bottom_frame, text="Quit", width=25, command=self.destroy)

        self.hit_button.pack(side=tk.LEFT, padx=(100, 200))
        self.stick_button.pack(side=tk.LEFT)

        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.game_screen.pack(side=tk.LEFT, anchor=tk.N)

        self.game_screen.setup_opening_animation()

    def show_next_round_options(self):
        self.hit_button.pack_forget()
        self.stick_button.pack_forget()

        self.next_round_button.pack(side=tk.LEFT, padx=(100, 200))
        self.quit_button.pack(side=tk.LEFT)

    def show_gameplay_buttons(self):
        self.next_round_button.pack_forget()
        self.quit_button.pack_forget()

        self.hit_button.pack(side=tk.LEFT, padx=(100, 200))
        self.stick_button.pack(side=tk.LEFT)

    def next_round(self):
        self.show_gameplay_buttons()
        self.game_state.next_round()
        self.display_table()

    def hit(self):
        self.game_state.hit()
        self.display_table()

    def stick(self):
        table_state = self.game_state.calculate_final_state()
        self.display_table(False, table_state)


class GameState:
    def __init__(self, player_name):
        self.BASE_BET = 5
        self.minimum_bet = self.BASE_BET
        self.current_round = 1
        self.pot = 0

        self.soundboard = SoundBoard()

        self.deck = Deck()
        self.deck.shuffle()
        # self.soundboard.shuffle_sound.play()

        self.player = Player(player_name)
        self.dealer = Dealer()

        self.begin_round()

    def begin_round(self):
        self.has_winner = ''

        for i in range(2):
            self.player.receive_card(self.deck.deal())
            self.dealer.receive_card(self.deck.deal())

        if self.player.can_place_bet(self.minimum_bet):
            self.player.place_bet(self.minimum_bet)
            self.dealer.place_bet(self.minimum_bet)
            self.add_bet(self.minimum_bet * 2)
        else:
            # player is out - game over
            pass

    def next_round(self):
        self.assign_winnings(self.has_winner)

        self.current_round += 1
        self.minimum_bet = self.BASE_BET * self.current_round
        print('mb', self.minimum_bet)

        self.player.empty_hand()
        self.dealer.empty_hand()

        self.begin_round()

    def add_bet(self, amount):
        print('adding', amount, 'to pot of', self.pot)
        self.pot += amount

    def assign_winnings(self, winner):
        if winner == 'p':
            self.player.add_winnings(self.pot)
            print('player wins, reset pot')
            self.pot = 0
        elif winner == 'd':
            self.dealer.add_winnings(self.pot)
            print('dealer wins, empty pot')
            self.pot = 0

    def hit(self):
        self.player.receive_card(self.deck.deal())
        if self.player.has_blackjack:
            self.has_winner = 'p'
        elif self.player.is_over:
            self.has_winner = 'd'

        return self.has_winner

    def get_table_state(self):
        blackjack = False
        winner = self.has_winner
        if not winner:
            winner = self.someone_has_blackjack()
            if winner:
                blackjack = True
        table_state = {
            'player_cards': self.player.cards,
            'dealer_cards': self.dealer.cards,
            'has_winner': winner,
            'blackjack': blackjack,
            'player_money': self.player.money
        }

        return table_state

    def calculate_final_state(self):
        player_hand_value = self.player.score
        dealer_hand_value = self.dealer.score

        if player_hand_value == dealer_hand_value:
            winner = 'dp'
        elif player_hand_value > dealer_hand_value:
            winner = 'p'
        else:
            winner = 'd'

        self.has_winner = winner

        table_state = {
            'player_cards': self.player.cards,
            'dealer_cards': self.dealer.cards,
            'has_winner': winner,
            'player_money': self.player.money
        }

        return table_state

    def player_score_as_text(self):
        return "Score: " + str(self.player.score)

    def player_money_as_text(self):
        return "Money: £" + str(self.player.money)

    def pot_money_as_text(self):
        return "Pot: £" + str(self.pot)

    def someone_has_blackjack(self):
        player = False
        dealer = False
        if self.player.has_blackjack:
            player = True
        if self.dealer.has_blackjack:
            dealer = True

        if player and dealer:
            return 'dp'
        elif player:
            return 'p'
        elif dealer:
            return 'd'

        return False


if __name__ == "__main__":
    gw = GameWindow()
    gw.mainloop()
