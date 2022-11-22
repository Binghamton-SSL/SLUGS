from django_unicorn.components import UnicornView
from gig.models import BingoBoard, TileOnBoard
from django.core.exceptions import ValidationError


class BingoboardView(UnicornView):
    board_id = None
    board = None
    bingoBoardError = None

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.board_id = kwargs.get("board_id")
        self.board = BingoBoard.objects.filter(pk=self.board_id).first()

    def toggle_tile(self, tile_pk, *args, **kwargs):
        if self.request == None:
            self.bingoBoardError = "Connection has been lost to the server. The bingo board is no longer updating in real time. Please refresh!"
            raise ValidationError("User is none")
        tile = TileOnBoard.objects.get(pk=tile_pk)
        if tile.checked_by is None:
            tile.checked_by = self.request.user
        else:
            tile.checked_by = None
        tile.save()