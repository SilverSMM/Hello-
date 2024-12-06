import json
import os
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from uuid import uuid4

TOKEN = "YOUR_BOT_TOKEN"

application = Application.builder().token(TOKEN).build()

# Start command to choose difficulty
async def start(update: Update, context):
    chat_id = update.message.chat_id
    message = "Let's play Tic Tac Toe! You are X, and the bot is O. Choose difficulty:"
    keyboard = [
        [InlineKeyboardButton("Easy", callback_data="difficulty_easy")],
        [InlineKeyboardButton("Medium", callback_data="difficulty_medium")],
        [InlineKeyboardButton("Hard", callback_data="difficulty_hard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

# Handle difficulty selection and edit message
async def handle_difficulty(update: Update, context):
    query = update.callback_query
    difficulty = query.data.split("_")[1]
    chat_id = query.message.chat_id

    context.user_data['difficulty'] = difficulty

    # Edit message to show mode set and button to start game
    await query.edit_message_text(text=f"Mode set to {difficulty.capitalize()}",
                                  reply_markup=InlineKeyboardMarkup(
                                      [[InlineKeyboardButton("Play Game", callback_data="start_game")]]))

# Start game when play game is clicked
async def start_game(update: Update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    reset_board(chat_id)
    await send_game_board(chat_id, context, query.message.message_id)

# Send game board
async def send_game_board(chat_id, context, message_id=None):
    board = load_board(chat_id)
    keyboard = [
        [InlineKeyboardButton(board[0] or ".", callback_data="0"),
         InlineKeyboardButton(board[1] or ".", callback_data="1"),
         InlineKeyboardButton(board[2] or ".", callback_data="2")],
        [InlineKeyboardButton(board[3] or ".", callback_data="3"),
         InlineKeyboardButton(board[4] or ".", callback_data="4"),
         InlineKeyboardButton(board[5] or ".", callback_data="5")],
        [InlineKeyboardButton(board[6] or ".", callback_data="6"),
         InlineKeyboardButton(board[7] or ".", callback_data="7"),
         InlineKeyboardButton(board[8] or ".", callback_data="8")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if message_id:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Tic Tac Toe", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Tic Tac Toe", reply_markup=reply_markup)

# Reset game board
def reset_board(chat_id):
    board = ["", "", "", "", "", "", "", "", ""]
    save_board(chat_id, board)

# Save game board to file
def save_board(chat_id, board):
    with open(f"board_{chat_id}.json", "w") as f:
        json.dump(board, f)

# Load game board from file
def load_board(chat_id):
    if os.path.exists(f"board_{chat_id}.json"):
        with open(f"board_{chat_id}.json", "r") as f:
            return json.load(f)
    return ["", "", "", "", "", "", "", "", ""]

# Handle moves and update the board
async def handle_move(update: Update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    callback_data = query.data
    board = load_board(chat_id)

    if board[int(callback_data)] == "":
        board[int(callback_data)] = "X"  # Player move

        if check_winner(board, "X"):
            await context.bot.send_message(chat_id=chat_id, text=f"You win, <a href='tg://user?id={update.effective_user.id}'>{update.effective_user.first_name}</a>!", parse_mode="HTML")
            reset_board(chat_id)
            await send_game_board(chat_id, context, message_id)
            return

        if is_board_full(board):
            await context.bot.send_message(chat_id=chat_id, text="It's a draw!")
            reset_board(chat_id)
            await send_game_board(chat_id, context, message_id)
            return

        difficulty = context.user_data.get('difficulty', 'easy')
        board = bot_move(board, difficulty)

        if check_winner(board, "O"):
            await context.bot.send_message(chat_id=chat_id, text="The bot wins!")
            reset_board(chat_id)
            await send_game_board(chat_id, context, message_id)
            return

        if is_board_full(board):
            await context.bot.send_message(chat_id=chat_id, text="It's a draw!")
            reset_board(chat_id)
            await send_game_board(chat_id, context, message_id)
            return

        save_board(chat_id, board)
        await send_game_board(chat_id, context, message_id)

# Check if player wins
def check_winner(board, player):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    return any(all(board[i] == player for i in combo) for combo in winning_combinations)

# Check if board is full
def is_board_full(board):
    return all(cell != "" for cell in board)

# Bot's move based on difficulty
def bot_move(board, difficulty):
    if difficulty == "easy":
        return random_bot_move(board)
    elif difficulty == "medium":
        return medium_bot_move(board)
    elif difficulty == "hard":
        return hard_bot_move(board)

# Random move for easy mode
def random_bot_move(board):
    available_moves = [i for i, x in enumerate(board) if x == ""]
    if available_moves:
        move = random.choice(available_moves)
        board[move] = "O"
    return board

# Medium difficulty logic (block player)
def medium_bot_move(board):
    blocking_move = find_winning_move(board, "X")
    if blocking_move is not None:
        board[blocking_move] = "O"
    else:
        board = random_bot_move(board)
    return board

# Hard difficulty logic (win or block)
def hard_bot_move(board):
    winning_move = find_winning_move(board, "O")
    if winning_move is not None:
        board[winning_move] = "O"
    else:
        board = medium_bot_move(board)
    return board

# Find winning move for the player
def find_winning_move(board, player):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for combo in winning_combinations:
        player_count = sum(1 for i in combo if board[i] == player)
        empty_index = next((i for i in combo if board[i] == ""), None)
        if player_count == 2 and empty_index is not None:
            return empty_index
    return None

# Command to directly send a game board
async def game(update: Update, context):
    chat_id = update.message.chat_id
    reset_board(chat_id)
    await send_game_board(chat_id, context)

# Add handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_difficulty, pattern="^difficulty_"))
application.add_handler(CallbackQueryHandler(start_game, pattern="^start_game"))
application.add_handler(CallbackQueryHandler(handle_move, pattern="^[0-8]$"))
application.add_handler(CommandHandler("game", game))

# Run the bot
if __name__ == '__main__':
    application.run_polling()
