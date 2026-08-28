import React from 'react';
import ELDLogSheet from './ELDLogSheet';

export default function HOSSummary({
  dailyLogs,
  tripData,
  selectedDayIndex,
  onSelectDayIndex,
  selectedEvent,
  onSelectEvent,
}) {
  if (!dailyLogs || dailyLogs.length === 0) return null;

  return (
    <ELDLogSheet
      dailyLogs={dailyLogs}
      tripData={tripData}
      selectedDayIndex={selectedDayIndex}
      onSelectDayIndex={onSelectDayIndex}
      selectedEvent={selectedEvent}
      onSelectEvent={onSelectEvent}
    />
  );
}
