#!python3
from stockfish import Stockfish
from termcolor import colored
import regex
# https://pypi.org/project/stockfish/

class ColorConst:
    # red, green, yellow, blue, magenta, cyan, white.
    # on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white
    # bold, dark, underline, blink, reverse, concealed.
    WHITE_PIECE = "red"
    BLACK_PIECE = "blue"
    BOARD_WHITE = "on_white"
    BOARD_BLACK = "on_yellow"
    FEN_BG = None
    
class Player:
    BLACK = "Black"
    WHITE = "White"

def main():
    params = {
        "Debug Log File": "",
        "Contempt": 0,
        "Min Split Depth": 0,
        "Threads": 4,                   # More threads will make the engine stronger, but should be kept at less than the number of logical processors on your computer.
        "Ponder": "true",               # Let stockfish ponder the next move while the opponent is thinking
        "Hash": 2048,                   # 1024 MB for the hash table - you may want to increase/decrease this, depending on how much RAM you want to use. Should also be kept as some power of 2.
        "MultiPV": 4,                   # Output the N best lines (principal variations, PVs) when searching. Leave at 1 for best performance.
        "Skill Level": 100,             # Lower the Skill Level in order to make Stockfish play weaker (see also UCI_LimitStrength). Internally, MultiPV is enabled, and with a certain probability depending on the Skill Level a weaker move will be played.
        "Move Overhead": 0,             # Assume a time delay of x ms due to network and GUI overheads. This is useful to avoid losses on time in those cases.
        "Minimum Thinking Time": 60,
        "Slow Mover": 200,              # Lower values will make Stockfish take less time in games, higher values will make it think longer.
        "UCI_Chess960": "false",
        "UCI_LimitStrength": "false",
        "UCI_Elo": 1350
    }
    stockfish = Stockfish(
        path="/home/paul/repositories/chess/stockfish/src/stockfish",
        depth=20,
        parameters=params
    )
    
    finished = False        # whether to exit the program or not
    history = []            # history of board positions
    cache = {}              # cache of values for board positions
    cache["pov"] = False
    cache["eval_moves"] = False
    while (not finished):
        print("="*60)
        fen = stockfish.get_fen_position()
        if (len(history) == 0 or history[-1] != fen):
            # new board position
            history.append(fen)
        print("FEN: " + getFen(stockfish))
        finished = menu(stockfish, history, cache)

def menu(stockfish: Stockfish, history: list, cache: dict) -> bool:
    menu = ["1. Get best Moves",
            "2. Move help",
            "3. Set board (FEN)",
            "4. Flip sides",
            "5. Revert",
            "6. Evaluate Board",
            f"7. Switch POV (Current: {'b' if cache['pov'] else 'w'})",
            f"8. Evaluate Moves (Current: {'Y' if cache['eval_moves'] else 'N'})",
            "9. Exit"
            ]
    board = getBoardStr(stockfish=stockfish, flip=cache["pov"]).split("\n")
    # find the longest line in the menu
    menuMaxLineLen = 0
    for menuLine in menu:
        menuMaxLineLen = menuMaxLineLen if menuMaxLineLen >= len(menuLine) else len(menuLine)
    # adjust menu lines for neatly printing the board
    for i in range (0, len(menu)):
        menu[i] = menu[i].ljust(menuMaxLineLen)
    # matchup menu with board string and print them side by side.
    sep = (" " * 4) + "|" + (" " * 4)
    for i in range (0, len(menu) if len(menu) > len(board) else len(board)):
        # loop over all the lines. Need to check every time if the index exists
        # print menu part
        if (i < len(menu)):
            print(menu[i], end="")
        else:
            print(" " * menuMaxLineLen, end="")
        # print board part
        if (i < len(board)):
            print(sep, end="")
            print(board[i])
        else:
            print() # print new line
    
    # user input handling
    selection = input("Selection or Move ?> ")
    if (selection == "1"):
        # bestMove = stockfish.get_best_move_time(60000)
        # print(f"Best: {bestMove} - {describeMove(stockfish, bestMove)}")
        moves = getBestMoves(stockfish, cache)
        for move in moves:
            score = move["Centipawn"]
            mate = move["Mate"]
            move = move["Move"]
            moveDesc = describeMove(stockfish, move, color=False).ljust(50)
            if mate != None:
                print(f"{move}: {moveDesc} - Mate in {mate}")
            else:
                print(f"{move}: {moveDesc} - White advantage {score}")
    elif (selection == "2"):
        print("Move either A to B (a1b3) or shorthand")
        print("Shorthand: [Piece][file][rank]['x']target | 'oo' | 'ooo'\n"
              "If piece is ommited, pawn is assumed.\n"
              "First file and/or rank indicate source field and may be ommited\n"
              "if only one piece of the indicated or inferred type can move to target.\n"
              "x indicates capture.\n"
              "Target in the form of file and rank.\n"
              "oo and ooo for king and queen side castling.\n"
              "For convenience pieces may be identified with lower case letters except for 'B'.\n"
              "Or use the full length moves src dst"
              )
    elif (selection == "3"):
        setPosition(stockfish, cache=cache)
    elif (selection == "4"):
        fen = stockfish.get_fen_position()
        white_turn = (fen.find(" w ") > 0)
        if (white_turn):
            fen = fen.replace(" w ", " b ")
        else:
            fen = fen.replace(" b ", " w ")
        stockfish.set_fen_position(fen, False)
    elif (selection == "5"):
        for i in range(0, len(history)):
            ni = i - len(history)
            print(f"{i} | {ni}: " + colorFen(history[i]))
        try:
            idx = int(input("ID ?> "))
            if (idx >= (-1 * len(history)) and idx < len(history)):
                stockfish.set_fen_position(history[idx], False)
            else:
                print("Invalid index.")
        except ValueError:
            print("Not a number.")
    elif (selection == "6"):
        print(getBoardStr(stockfish=stockfish, flip=cache["pov"], cache=cache))
    elif (selection == "7"):
        flipPov(cache)
    elif (selection == "8"):
        flipEvalMoves(cache)
    elif (selection == "9"):
        return True
    else:
        move = selection
        evaluateMove(stockfish, move, cache)
    return False

def flipPov(cache: dict):
    cache["pov"] = not cache["pov"]

def flipEvalMoves(cache: dict):
    cache["eval_moves"] = not cache["eval_moves"]

# Shows move preview if valid, otherwise reports error
def evaluateMove(stockfish: Stockfish, move: str, cache: dict):
    move = resolveMove(stockfish, move)
    if (stockfish.is_move_correct(move)):
        desc = describeMove(stockfish, move) # describe move for later (because we update the board)
        highlight = [move[0:2], move[2:4]]
        fen = stockfish.get_fen_position() # backup board state
        if cache["eval_moves"]:
            ntm = getNTM(stockfish)
            # calculate the difference between the advantages before and after the move
            eval_before = getEval(stockfish, cache)
            stockfish.make_moves_from_current_position([move])
            eval_after = getEval(stockfish, cache)
            # generate a rating for the move
            rating = eval_after["value"] - eval_before["value"]
            if (ntm == Player.BLACK):
                # ntm is from before the move so we get the rating
                # for the player who makes the move
                rating = rating * -1
            print(getBoardStr(stockfish, flip=cache["pov"], highlight=highlight, cache=cache))
            print(f"Before: {eval_before}\n"
                  f" After: {eval_after}\n"
                  f"Move Rating for {ntm}: {rating}")
        else:
            stockfish.make_moves_from_current_position([move])
            print(getBoardStr(stockfish, flip=cache["pov"], highlight=highlight))
        print(desc)
        print("Play move?")
        choice = ask()
        if not choice:
            # reset the board to the previous state but don't clear cache
            stockfish.set_fen_position(fen, False)
    else:
        print(f"Error: {move}")

def resolveMove(stockfish: Stockfish, move: str, color: bool = True) -> str:
    # turn shorthand notation into valid moves for stockfish
    # "e4" = pawn to e4
    # "xe4" = pawn captures e4
    # "bxc5" = pawn in b file captures c5
    # "Bxc5" = bishop captures c5
    # "Bbxc5" = bishop in b file captures c5 (because another bishop could also capture c5)
    # "B3xd4" = bishop from rank 3 captures d4 (because another bishop from the same file could also capture)
    # "ra6" = rook to a6
    # "rfa6" = rook in f file (f6) to a6
    # "qxf4" = queen captures f4
    # "d2d1q" = pawn from d2 to d1 turns into a queen
    # "d2e1q" = pawn from d2 captures e1 and turns into a queen
    move = move.replace(" ", "").replace("-", "")
    ntm = getNTM(stockfish)
    if len(move) == 0:
        return "Empty move"
    if regex.match("^(?:[a-h][1-8]){2}[qrnb]$", move.lower()):
        move = move.lower()
        if stockfish.is_move_correct(move):
            return move
        else:
            return "Invalid move."
    else:
        # castling
        if (move.lower() == 'oo'):
            # castle king side
            # need to check if it's actually a king there as another piece could also have a valid move.
            if ntm == Player.WHITE and stockfish.get_what_is_on_square("e1") == Stockfish.Piece.WHITE_KING:
                move = "e1g1"
            elif ntm == Player.BLACK and stockfish.get_what_is_on_square("e8") == Stockfish.Piece.BLACK_KING:
                move = "e8g8"
            else:
                move = "Invalid"
            if stockfish.is_move_correct(move):
                return move
            else:
                return "Can not castle king side."
        elif (move.lower() == 'ooo'):
            # castle queen side
            if ntm == Player.WHITE and stockfish.get_what_is_on_square("e1") == Stockfish.Piece.WHITE_KING:
                move = "e1c1"
            elif ntm == Player.BLACK and stockfish.get_what_is_on_square("e8") == Stockfish.Piece.BLACK_KING:
                move = "e8c8"
            else:
                move = "Invalid"
            if stockfish.is_move_correct(move):
                return move
            else:
                return "Can not castle queen side."
        
        # resolve the rest with regex
        # do not allow lower case 'b' in first group because it conflicts with second group
        # allow other lower case letters for convenience
        match = regex.match("^([RNBKQrnkq]?)([a-h]?)([1-8]?)(x?)([a-h][1-8])(=?[RNBKQrnbkq]?)$", move)
        if match == None:
            return "Not a valid move string."
        groups = match.groups()
        piece = None
        
        # resolve piece class
        if len(groups[0]) == 0:
            piece = Stockfish.Piece.WHITE_PAWN if ntm == Player.WHITE else Stockfish.Piece.BLACK_PAWN
        else:
            if groups[0].lower() == 'r':
                piece = Stockfish.Piece.WHITE_ROOK if ntm == Player.WHITE else Stockfish.Piece.BLACK_ROOK
            elif groups[0] == 'B': # bxc6 is a pawn from b, not a bishop.
                piece = Stockfish.Piece.WHITE_BISHOP if ntm == Player.WHITE else Stockfish.Piece.BLACK_BISHOP
            elif groups[0].lower() == 'n':
                piece = Stockfish.Piece.WHITE_KNIGHT if ntm == Player.WHITE else Stockfish.Piece.BLACK_KNIGHT
            elif groups[0].lower() == 'k':
                piece = Stockfish.Piece.WHITE_KING if ntm == Player.WHITE else Stockfish.Piece.BLACK_KING
            elif groups[0].lower() == 'q':
                piece = Stockfish.Piece.WHITE_QUEEN if ntm == Player.WHITE else Stockfish.Piece.BLACK_QUEEN
            else:
                return f"Can not determine piece to move ('{groups[0]}')."
        
        # resolve source file
        src_file = None
        if len(groups[1]) == 1:
            src_file = groups[1]
        
        # resolve source rank
        src_rank = None
        if len(groups[2]) == 1:
            src_rank = groups[2]
        
        # resolve capture
        isCapture = groups[3] == 'x'
        
        # pawn conversion
        turnsInto = groups[5].lstrip('=')
        
        # resolve dst
        dst = groups[4]
        
        # resolve src
        src = None
        # find src
        if src_file != None and src_rank != None:
            src = f"{src_file}{src_rank}"
        else:
            possibleSrc = []
            # run through all the squares and check all the pieces if they can move to the square
            for file in range(ord('a'), ord('h') + 1):
                file = chr(file)
                if src_file != None and src_file != file:
                    continue
                for rank in range(1,8+1):
                    rank = str(rank)
                    if src_rank != None and src_rank != rank:
                        continue
                    src = f"{file}{rank}"
                    if piece == stockfish.get_what_is_on_square(src) and stockfish.is_move_correct(f"{src}{dst}{turnsInto}"):
                        possibleSrc.append(src)
            if len(possibleSrc) == 1:
                src = possibleSrc[0]
            elif len(possibleSrc) == 0:
                pieceDesc = str(piece).replace("Piece.", "")
                if color:
                    pieceDesc = colored(pieceDesc, color=ColorConst.WHITE_PIECE if ntm == Player.WHITE else ColorConst.BLACK_PIECE, on_color=ColorConst.FEN_BG, attrs=['bold'])
                if src_rank != None and src_file == None:
                    pieceDesc = pieceDesc + f" from rank {src_rank}"
                elif src_rank == None and src_file != None:
                    pieceDesc = pieceDesc + f" from file {src_file}"
                # no need to check for both since that is already covered above
                # no need to check for neither since no additional description is needed
                return f"No {pieceDesc} can go to {dst}"
            else:
                pieceDesc = str(piece).replace("Piece.", "")
                if color:
                    pieceDesc = colored(pieceDesc, color=ColorConst.WHITE_PIECE if ntm == Player.WHITE else ColorConst.BLACK_PIECE, on_color=ColorConst.FEN_BG, attrs=['bold'])                
                return f"Could not determine which {pieceDesc} you want to move to {dst}"
        # build stockfish move
        move = f"{src}{dst}{turnsInto}"
        # check if resolved move is indeed a capture
        if stockfish.is_move_correct(move):
            if ((isCapture and turnsInto != '' and stockfish.get_what_is_on_square(dst) == None) or (isCapture and turnsInto == '' and stockfish.will_move_be_a_capture(move) == Stockfish.Capture.NO_CAPTURE)):
                return "Move is no Capture"
            elif (not isCapture and turnsInto != '' and stockfish.get_what_is_on_square(dst) != None) or (not isCapture and turnsInto == '' and stockfish.will_move_be_a_capture(move) != Stockfish.Capture.NO_CAPTURE):
                print("Warning: Move results in a capture, but capture was not indicated by the move string.")
            return move
    return "Invalid Move"

def describeMove(stockfish: Stockfish, move: str, color: bool = True) -> str:
    if (stockfish.is_move_correct(move)):
        # move stuff
        src = move[0:2]
        dst = move[2:4]
        turnsInto = move[4:5].lower()
        cap = None
        pieceMoving = str(stockfish.get_what_is_on_square(src)).replace("Piece.", "")        
        attrs = ['bold']
        fg, bg = None, None
        tgt_fg, tgt_bg = ColorConst.FEN_BG, ColorConst.FEN_BG
        if color:
            if getNTM(stockfish) == Player.WHITE:
                fg = ColorConst.WHITE_PIECE
                tgt_fg = ColorConst.BLACK_PIECE
            else:
                fg = ColorConst.BLACK_PIECE
                tgt_fg = ColorConst.WHITE_PIECE
            pieceMoving = colored(pieceMoving, fg, bg, attrs)
        
        ret = f"{pieceMoving} from {src} to {dst}"
        
        # if capture
        cap = stockfish.will_move_be_a_capture(move)
        
        if cap == Stockfish.Capture.DIRECT_CAPTURE:
            tgt = stockfish.get_what_is_on_square(dst)
            tgt = str(tgt).replace("Piece.", "")
            if (color):
                tgt = colored(tgt, color=tgt_fg, on_color=tgt_bg, attrs=attrs)
            ret = ret + f" capturing {tgt}"
        elif cap == Stockfish.Capture.EN_PASSANT:
            tgt = Stockfish.Piece.WHITE_PAWN if getNTM(stockfish) == Player.BLACK else Stockfish.Piece.BLACK_PAWN
            tgt = str(tgt).replace("Piece.", "")
            if (color):
                tgt = colored(tgt, color=tgt_fg, on_color=tgt_bg, attrs=attrs)            
            ret = ret + f" capturing {tgt} en passant"

        # turning pawn into something else.
        if turnsInto != '':
            if turnsInto == 'q':
                turnsInto = Stockfish.Piece.WHITE_QUEEN if getNTM(stockfish) == Player.WHITE else Stockfish.Piece.BLACK_QUEEN
            elif turnsInto == 'n':
                turnsInto = Stockfish.Piece.WHITE_KNIGHT if getNTM(stockfish)== Player.WHITE else Stockfish.Piece.BLACK_KNIGHT
            elif turnsInto == 'b':
                turnsInto = Stockfish.Piece.WHITE_BISHOP if getNTM(stockfish)== Player.WHITE else Stockfish.Piece.BLACK_BISHOP
            elif turnsInto == 'r':
                turnsInto = Stockfish.Piece.WHITE_ROOK if getNTM(stockfish)== Player.WHITE else Stockfish.Piece.BLACK_ROOK
            # remove 'Piece.'
            turnsInto = str(turnsInto).replace('Piece.', '')
            # color
            if color:
                turnsInto = colored(turnsInto, color=ColorConst.WHITE_PIECE if getNTM(stockfish) == Player.WHITE else ColorConst.BLACK_PIECE, on_color=ColorConst.FEN_BG, attrs=['bold'])
            if cap != None:
                ret = ret + " and"
            ret = ret + f" turning into {turnsInto}"
        return ret
    else:
        return "Invalid Move"

def setPosition(stockfish: Stockfish, cache: dict):
    print("https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation")
    print("Small letters are black. Possible pieces: R, N, B, Q, K, P")
    print("Numbers denote empty spaces. Rows are delimited by '/'")
    print("Next is whose turn it is. 'w' or 'b'")
    print("Then possible castlings. K or Q for king's or queen's side. '-' for none.")
    print("Then the en passant target square, even if such a move is not possible. '-' for none")
    print("Then the number of the current half turn since last capture. 0 if unsure.")
    print("Finally the number of the next turn. 1 if unsure.")
    print("Leave empty to not do anything to the current board.")
    correct = False
    while not correct:
        fen = input("FEN ?> ")
        if (len(fen) == 0):
            correct = True # abort without changing the board.
        else:
            old_fen = stockfish.get_fen_position()
            try:
                fenPass(fen)
                stockfish.set_fen_position(fen, False)
                print(getBoardStr(stockfish, flip=cache["pov"]))
                print("Correct?")
                choice = ask()
                if choice:
                    stockfish.set_fen_position(fen, True)
                    correct = True
                else:
                    stockfish.set_fen_position(old_fen, False)
                    correct = False
            except ValueError as ex:
                print("Invalid position.")
                print(ex)
                correct = False

def getBoardStr(stockfish: Stockfish, flip: bool = False, highlight: list[str] = [], cache = None, color = True) -> str:
    # unfliped A8 is top left
    range_ranks = range(1, 8 + 1) if flip else range(8, 1 - 1, -1)
    range_files = range(ord('a'), ord('h') + 1) if not flip else range(ord('h'), ord('a') - 1, -1)
    white_squre = True # first square is white regardless of orientation
    lineSep = "  " + (("+---" * 9)[:-3]) # the seperator between the lines on the board.
    
    result = " " # spacing for header to line up right
    # make files header
    for file in range_files:
        file = chr(file)
        result = result + f"   {file}"
    result = result.rstrip() + "\n"
    
    # print actual board
    for rank in range_ranks:
        result = result + lineSep + "\n"
        result = result + f"{rank} |"
        for file in range_files:
            file = chr(file)
            sqr = f"{file}{rank}"
            piece = stockfish.get_what_is_on_square(sqr)
            fieldStr = "   " if piece == None else f" {piece.value} "
            if color:
                fg = None
                bg = ColorConst.BOARD_WHITE if white_squre else ColorConst.BOARD_BLACK
                attrs = ['bold']
                if sqr in highlight:
                    attrs.append('reverse')
                if piece != None:
                    if piece.value in ['r', 'n', 'b', 'q', 'k', 'p']:
                        fg = ColorConst.BLACK_PIECE
                    else:
                        fg = ColorConst.WHITE_PIECE
                fieldStr = colored(fieldStr, color=fg, on_color=bg, attrs=attrs)
            result = result + f"{fieldStr}|"
            white_squre = not white_squre
        result = result + f" {rank}\n"
        white_squre = not white_squre
    result = result + lineSep + "\n"
    
    # make files footer
    result = result + " " # spacing for footer to line up right
    for file in range_files:
        file = chr(file)
        result = result + f"   {file}"
    result = result.rstrip() + "\n"
    
    # more description stuffs
    result = result + getFen(stockfish, color) + "\n"
    result = result + f"Next to move: {getNTM(stockfish)}\n"
    if (not cache is None):
        result = result + f"Evaluation (Positive is advantage for White):\n{str(getEval(stockfish, cache))}\n"
        result = result + f"Win/Draw/Loose stats for {getNTM(stockfish)}\n{str(getWDL(stockfish, cache))}\n"
    return result

def getWDL(stockfish: Stockfish, cache: dict) -> list:
    key = "wdl"
    fen = stockfish.get_fen_position()
    if not (fen in cache and key in cache[fen]):
        if not fen in cache:
            cache[fen] = {}
        cache[fen][key] = stockfish.get_wdl_stats() if stockfish.does_current_engine_version_have_wdl_option() else [0,0,0]
    return cache[fen][key]

def getBestMoves(stockfish: Stockfish, cache: dict, moves: int = 0) -> list[dict]:
    key = "best_moves"
    if moves <= 0:
        moves = stockfish.get_parameters()["MultiPV"]
    fen = stockfish.get_fen_position()
    if not (fen in cache and key in cache[fen]):
        if not fen in cache:
            cache[fen] = {}
        cache[fen][key] = stockfish.get_top_moves(moves)
    return cache[fen][key]

def getEval(stockfish: Stockfish, cache: dict) -> dict:
    key = "eval"
    fen = stockfish.get_fen_position()
    if not (fen in cache and key in cache[fen]):
        if not fen in cache:
            cache[fen] = {}
        cache[fen][key] = stockfish.get_evaluation()
    return cache[fen][key]

def getNTM(stockfish: Stockfish) -> str:
    return Player.WHITE if (stockfish.get_fen_position().find(" w ") > 0) else Player.BLACK

def getFen(stockfish: Stockfish, color: bool = True) -> str:
    fen = stockfish.get_fen_position()
    if color:
        return colorFen(fen)
    else:
        return fen

def colorFen(fen: str) -> str:
    coloredFen = ""
    attrs=['bold']
    for c in fen:
        cc = c
        if cc in ['R','N','B','Q','K','P', 'w']:
            cc = colored(c, color=ColorConst.WHITE_PIECE, on_color=ColorConst.FEN_BG, attrs=attrs)
        elif cc in ['r','n','b','q','k','p']:
            cc = colored(c, color=ColorConst.BLACK_PIECE, on_color=ColorConst.FEN_BG, attrs=attrs)
        else:
            cc = colored(c, color=None, on_color=ColorConst.FEN_BG, attrs=attrs)
        coloredFen = coloredFen + cc
    return coloredFen

def fenPass(fen):
    regexMatch=regex.match('\s*^(((?:[rnbqkpRNBQKP1-8]+\/){7})[rnbqkpRNBQKP1-8]+)\s([b|w])\s([K|Q|k|q]{1,4}|-)\s(-|[a-h][1-8])\s(\d+\s\d+)$', fen)
    if  regexMatch:
        regexList = regexMatch.groups()
        fen = regexList[0].split("/")
        if len(fen) != 8:
            raise ValueError("expected 8 rows in position part of fen: {0}".format(repr(fen)))
        
        white_king = False
        black_king = False
        for fenPart in fen:
            field_sum = 0
            previous_was_digit = False

            for c in fenPart:
                if c in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                    if previous_was_digit:
                        raise ValueError("two subsequent digits in position part of fen: {0}".format(repr(fen)))
                    field_sum += int(c)
                    previous_was_digit = True
                elif c.lower() in ["p", "n", "b", "r", "q", "k"]:
                    field_sum += 1
                    previous_was_digit = False
                    if c == "K" and not white_king:
                        white_king = True
                    elif c == "k" and not black_king:
                        black_king = True
                    elif c == "K" and white_king:
                        raise ValueError("Multiple white kings.")
                    elif c == "k" and black_king:
                        raise ValueError("Multiple black kings.")
                else:
                    raise ValueError("invalid character in position part of fen: {0}".format(repr(fen)))
            # end for in fenPart
        # end for in fen
        if field_sum != 8:
            raise ValueError("expected 8 columns per row in position part of fen: {0}".format(repr(fen)))
        if not black_king:
            raise ValueError("Black king not present.")
        if not white_king:
            raise ValueError("White king not present.")
    else: # else regex doesn't match
        raise ValueError("fen doesn`t match follow this example: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 ")

def ask(defaultTrue: bool = True) -> bool:
    if defaultTrue:
        answer = input("Y/n ?> ")
        if answer == '' or answer[0].lower() != 'n':
            return True
        else:
            return False
    else:
        answer = input("y/N ?> ")
        if anwer == '' or answer[0].lower() != 'y':
            return False
        else:
            return True

if __name__ == "__main__":
    main()
