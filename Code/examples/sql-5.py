# NOTE: I did *NOT* add a shebang here, intentionally, because
#       this is *NEVER* supposed to be a user-facing script!



class FormError(BaseException):
    def __init__(this, msg):
        this.msg = msg



def get_game_info(conn, game):
    # get the basic game properties
    cursor = conn.cursor()
    cursor.execute("SELECT player1,player2,size,state FROM games WHERE id = %d;" % game)
    if cursor.rowcount != 1:
        raise FormError("Invalid game ID")

    row = cursor.fetchall()[0]
    players = [row[0],row[1]]
    size    =  row[2]
    state   =  row[3]

    if state is None:
         state = "Active"

    cursor.close()

    return (players,size,state)



def build_board(conn, game,size):
    # we'll build the empty board, and then fill in with the move list that
    # we get from the DB.
    board = []
    for i in range(size):
        board.append([""]*size)


    # search for all moves that have happenend during this game.
    cursor = conn.cursor()
    cursor.execute("SELECT x,y,letter FROM moves WHERE gameID = %d;" % game)

    counts = {"X":0, "O":0}
    for move in cursor.fetchall():
        (x,y,letter) = move

        x = int(x)
        y = int(y)
        assert x >= 0 and x < size
        assert y >= 0 and y < size

        assert letter in "XO"

        assert board[x][y] == ""
        board[x][y] = letter

        counts[letter] += 1

    cursor.close()

    assert counts["X"] >= counts["O"]
    assert counts["X"] <= counts["O"]+1

    if counts["X"] == counts["O"]:
        nextPlayer = 0
    else:
        nextPlayer = 1
    letter = "XO"[nextPlayer]

    return (board,nextPlayer,letter)

