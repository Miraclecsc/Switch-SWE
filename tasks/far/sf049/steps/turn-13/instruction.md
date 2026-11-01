Also, We are calling `times` here and `chain` on the event? I see why. It reads like "click button 2 times". But it feels inconsistent.

A generated Click requires a matching MouseDown/MouseUp on the same widget and button. Consume the pending press once; unmatched or duplicate releases must not generate extra clicks. Test native App.on_event processing, not only Pilot which bypasses it.