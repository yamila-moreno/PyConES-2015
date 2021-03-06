# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.core.exceptions import ObjectDoesNotExist

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from markupfield.fields import MarkupField
from proposals.models import ProposalBase



@python_2_unicode_compatible
class Schedule(models.Model):

    section = models.OneToOneField("conference.Section")
    published = models.BooleanField(default=True)
    hidden = models.BooleanField("Hide schedule from overall conference view", default=False)

    class Meta:
        ordering = ["section"]

    def __str__(self):
        return "%s Schedule" % self.section


@python_2_unicode_compatible
class Day(models.Model):

    schedule = models.ForeignKey(Schedule)
    date = models.DateField()

    def __str__(self):
        return "%s" % self.date

    class Meta:
        unique_together = [("schedule", "date")]
        ordering = ["date"]


@python_2_unicode_compatible
class Room(models.Model):

    schedule = models.ForeignKey(Schedule)
    name = models.CharField(max_length=65)
    order = models.PositiveIntegerField()

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class SlotKind(models.Model):
    """
    A slot kind represents what kind a slot is. For example, a slot can be a
    break, lunch, or X-minute talk.
    """

    schedule = models.ForeignKey(Schedule)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


@python_2_unicode_compatible
class Slot(models.Model):

    day = models.ForeignKey(Day)
    kind = models.ForeignKey(SlotKind)
    start = models.TimeField()
    end = models.TimeField()
    content_override = MarkupField(blank=True)

    def assign(self, content):
        """
        Assign the given content to this slot and if a previous slot content
        was given we need to unlink it to avoid integrity errors.
        """
        self.unassign()
        content.slot = self
        content.save()

    def unassign(self):
        """
        Unassign the associated content with this slot.
        """
        content = self.content
        if content and content.slot_id:
            content.slot = None
            content.save()

    @property
    def content(self):
        """
        Return the content this slot represents.
        @@@ hard-coded for presentation for now
        """
        try:
            return self.content_ptr
        except ObjectDoesNotExist:
            return None

    @property
    def start_datetime(self):
        return datetime.datetime(
            self.day.date.year,
            self.day.date.month,
            self.day.date.day,
            self.start.hour,
            self.start.minute)

    @property
    def end_datetime(self):
        return datetime.datetime(
            self.day.date.year,
            self.day.date.month,
            self.day.date.day,
            self.end.hour,
            self.end.minute)

    @property
    def length_in_minutes(self):
        return int(
            (self.end_datetime - self.start_datetime).total_seconds() / 60)

    @property
    def rooms(self):
        return Room.objects.filter(pk__in=self.slotroom_set.values("room"))

    def __str__(self):
        return "%s %s (%s - %s)" % (self.day, self.kind, self.start, self.end)

    class Meta:
        ordering = ["day", "start", "end"]


@python_2_unicode_compatible
class SlotRoom(models.Model):
    """
    Links a slot with a room.
    """

    slot = models.ForeignKey(Slot)
    room = models.ForeignKey(Room)

    def __str__(self):
        return "%s %s" % (self.room, self.slot)

    class Meta:
        unique_together = [("slot", "room")]
        ordering = ["slot", "room__order"]


@python_2_unicode_compatible
class Presentation(models.Model):

    slot = models.OneToOneField(Slot, null=True, blank=True, related_name="content_ptr")
    title = models.CharField(max_length=100)
    description = MarkupField()
    abstract = MarkupField()
    speaker = models.ForeignKey("speakers.Speaker", related_name="presentations")
    additional_speakers = models.ManyToManyField("speakers.Speaker", related_name="copresentations",
                                                 blank=True)
    cancelled = models.BooleanField(default=False)
    proposal_base = models.OneToOneField("proposals.ProposalBase", related_name="presentation")
    section = models.ForeignKey("conference.Section", related_name="presentations")

    @property
    def number(self):
        return self.proposal.number

    @property
    def proposal(self):
        if self.proposal_base_id is None:
            return None
        return ProposalBase.objects.get_subclass(pk=self.proposal_base_id)

    def speakers(self):
        yield self.speaker
        for speaker in self.additional_speakers.all():
            if speaker.user:
                yield speaker

    def __str__(self):
        return "#%s %s (%s)" % (self.number, self.title, self.speaker)

    class Meta:
        ordering = ["slot"]
