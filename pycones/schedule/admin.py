# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from schedule.models import Schedule, Day, Room, SlotKind, Slot, SlotRoom, Presentation

admin.site.register(Schedule)
admin.site.register(Day)
admin.site.register(Room)
admin.site.register(SlotKind)
admin.site.register(
    Slot,
    list_display=("day", "start", "end", "kind")
)
admin.site.register(
    SlotRoom,
    list_display=("slot", "room")
)
admin.site.register(Presentation)

