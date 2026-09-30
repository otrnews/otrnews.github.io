"""
Free CDL knowledge courses on OTR News.
Each lesson's "quiz" lists question numbers from QUIZ in build.py (0 = first question).
Lesson text is general study material based on the standard state CDL manual. It is not ELDT training.
Edit wording here; build.py turns it into pages at /courses/.
"""

COURSES = [
    {
        "slug": "general-knowledge",
        "title": "CDL General Knowledge",
        "blurb": "Inspections, safe driving, emergencies, and the rules every CDL driver must know.",
        "lessons": [
            {
                "slug": "vehicle-inspection",
                "title": "Inspecting your vehicle",
                "quiz": [8, 18, 19],
                "body": """
A good inspection finds problems before they turn into a breakdown, a crash, or an out-of-service order. You'll inspect before every trip, check again during the trip, and inspect after the trip.

## The seven-step inspection

The CDL manual teaches a seven-step method so you check the same things in the same order every time:

- **Step 1: Vehicle overview.** Walk up to the truck and look for leaks, damage, and anything leaning. Check the last inspection report.
- **Step 2: Engine compartment.** Check oil, coolant, power steering fluid, belts, hoses, and wiring.
- **Step 3: Start the engine and inspect inside the cab.** Check gauges, mirrors, windshield, wipers, horn, and emergency equipment.
- **Step 4: Turn off the engine and check the lights.** Headlights, four-way flashers, and clearance lights.
- **Step 5: Walk-around inspection.** Tires, wheels, rims, suspension, brakes, doors, and cargo securement.
- **Step 6: Check signal lights.** Turn signals and brake lights.
- **Step 7: Start the engine and check the brake system.** Parking brake, service brakes, and air brake checks if you have them.

## Tires

Look for bad wear, cuts, bulges, and low pressure. Minimum tread depth is **4/32 inch** in every major groove on the front (steering) tires and **2/32 inch** on all other tires. Don't run mismatched sizes or radial and bias-ply tires on the same axle.

## Checking cargo during the trip

Cargo shifts once the truck is moving. Check your cargo and securement **within the first 50 miles** of a trip. After that, check it every 3 hours or 150 miles, whichever comes first, and after every break.

## Tie-downs

The CDL manual's rule of thumb is **at least one tie-down for every 10 feet of cargo**, and never fewer than two, no matter how small the load. Tie-downs must be strong enough and in good condition.

**Key takeaway:** Inspect the same way every time, and recheck your load early in the trip.
""",
            },
            {
                "slug": "seeing-space-speed",
                "title": "Seeing, space, and speed",
                "quiz": [7, 4, 11, 10, 9, 12, 13, 17],
                "body": """
Most crashes come down to three things: not seeing a hazard in time, not leaving enough space, or going too fast for conditions.

## Look far ahead

Look **12 to 15 seconds ahead**. At highway speed that's about a quarter mile. Looking far ahead gives you time to slow down or change lanes before you're in trouble. Check your mirrors regularly, and more often around lane changes, merges, and intersections.

## Following distance

A loaded truck needs far more room to stop than a car. At speeds **below 40 mph**, leave at least **one second for every 10 feet of vehicle length**. A 70-foot rig needs 7 seconds. Above 40 mph, add one more second.

## Stopping distance

Total stopping distance has three parts:

- **Perception distance:** how far you travel between seeing a hazard and your brain recognizing it.
- **Reaction distance:** how far you travel while moving your foot to the brake.
- **Braking distance:** how far the truck travels once the brakes are applied.

Speed matters more than most drivers think. **If you double your speed, your braking distance becomes about four times as long.**

## Wet roads and skids

Water can lift your tires off the road, called hydroplaning, at speeds **as low as 30 mph**, especially with worn tires or low pressure. **Most serious skids are caused by driving too fast for road conditions.** Slow down on wet, icy, or snowy roads before you need to.

## Getting out of trouble

When something appears ahead, **steering around it is usually faster than stopping**, because a heavy truck can't always stop in the space you have. Don't brake while you're turning sharply, since that can lock the wheels.

## Night driving

Use high beams when it's safe, but **dim them within 500 feet** of an oncoming vehicle or one you're following.

**Key takeaway:** Look far ahead, leave extra space, and set your speed for the conditions, not the limit.
""",
            },
            {
                "slug": "hazards-and-emergencies",
                "title": "Hazards, grades, and emergencies",
                "quiz": [5, 6, 14, 15, 16],
                "body": """
Some situations are dangerous every time, and the CDL test expects you to know exactly how to handle them.

## Stopped on the road

Turn on your four-way flashers right away, and put out your warning triangles **within 10 minutes** of stopping.

- **Two-lane road with traffic both ways:** one triangle within 10 feet of the vehicle on the traffic side, one about 100 feet behind, and one about 100 feet ahead.
- **One-way road or divided highway:** place them about 10 feet, 100 feet, and 200 feet behind the vehicle, toward approaching traffic.
- **Hill, curve, or anything blocking the view:** move the rear triangle back as far as 500 feet so drivers see it in time.

## Mountain driving

Gravity makes a loaded truck speed up on a downgrade. **Choose a lower gear before you start down the grade**, not after you're picking up speed. A common rule is to use the same gear you would need to climb that hill. Use the brakes to control speed, not to make up for being in too high a gear.

## Railroad crossings

Never stop on the tracks, and make sure there is room to clear them completely before you start across. With a manual transmission, **never shift gears while crossing the tracks**. Getting stuck in neutral on a crossing can be deadly.

## Right turns

Turn slowly and **keep the rear of the vehicle close to the curb** so cars can't squeeze in on your right. If you need extra room, swing wide as you complete the turn, not before you start it.

**Key takeaway:** Get the triangles out within 10 minutes, gear down before the grade, and never shift on the tracks.
""",
            },
            {
                "slug": "rules-for-cdl-drivers",
                "title": "Rules every CDL driver must follow",
                "quiz": [0, 1, 2, 3, 20, 21],
                "body": """
CDL drivers are held to stricter rules than other drivers. Breaking them can cost you your license and your job.

## Alcohol

The legal limit for a commercial driver is **0.04% blood alcohol concentration**, half the limit for most car drivers. A driver with any detectable alcohol, even under 0.04%, is placed out of service for 24 hours. Refusing a test counts the same as failing it.

## Hours of service

These are the main limits for property-carrying drivers:

- **11 hours of driving** after 10 consecutive hours off duty.
- **No driving after the 14th hour** since coming on duty. Breaks don't stop this clock.
- **A 30-minute break** after 8 cumulative hours of driving.
- **60/70-hour limit:** no driving after 60 hours on duty in 7 days, or 70 hours in 8 days. A 34-hour restart resets that clock.

## Phones

**Using a hand-held phone while driving a CMV is prohibited**, and so is texting. Hands-free use with a single touch is allowed, but the safest choice is to wait until you're parked.

## Medical certificate

You need a valid DOT medical examiner's certificate to drive a CMV. It can be valid for **up to 24 months**, and the examiner may issue it for a shorter time if you have a condition that needs monitoring.

**Key takeaway:** 0.04% alcohol, 11 and 14 hours, no hand-held phones, and keep your medical card current.
""",
            },
        ],
    },
    {
        "slug": "air-brakes",
        "title": "CDL Air Brakes",
        "blurb": "How air brakes work, how to inspect them, and how to use them safely on the road.",
        "lessons": [
            {
                "slug": "how-air-brakes-work",
                "title": "How the air brake system works",
                "quiz": [22, 23, 24, 29, 30, 35],
                "body": """
Air brakes use compressed air instead of fluid to apply the brakes. Knowing each part helps you inspect the system and spot trouble early.

## Making and storing air

- **Air compressor:** pumps air into the storage tanks. It's driven by the engine.
- **Governor:** controls the compressor. It stops the compressor from pumping, called cut-out, at **about 125 psi**. It lets the compressor start pumping again, called cut-in, at **about 100 psi**.
- **Air tanks:** hold the compressed air, enough to stop the truck several times even if the compressor stops working.
- **Safety valve:** keeps the tanks from getting too much pressure. It is usually set to open at 150 psi.

## Keeping the air clean and dry

Compressed air picks up water and oil, which can freeze and make brakes fail. **Tanks with manual drains should be drained at the end of each day of driving.** Some trucks have automatic drains.

An **alcohol evaporator** puts alcohol into the air system to **reduce the risk of ice in the brake valves** in cold weather. Check and fill the alcohol level every day in cold weather.

## Gauges and warnings

- **Supply pressure gauge:** shows how much pressure is in the air tanks.
- **Application pressure gauge:** shows how much air you are putting into the brakes when you press the pedal.
- **Low air pressure warning:** a light or buzzer that must come on **before pressure in the service tanks falls below 60 psi**.

**Key takeaway:** The governor works between about 100 and 125 psi, tanks get drained daily, and the low air warning must come on before 60 psi.
""",
            },
            {
                "slug": "spring-brakes",
                "title": "Spring brakes and parking",
                "quiz": [25, 33],
                "body": """
Spring brakes are your safety net. Air pressure holds them off while you drive. If the air leaks away, powerful springs put the brakes on by themselves.

## When spring brakes apply

In most vehicles, the spring brakes come on automatically when air pressure drops to **somewhere between 20 and 45 psi**. That is why losing air is serious: the truck will start braking on its own, possibly at a bad time and place.

That's also why the low air warning comes on at a higher pressure, before 60 psi. It gives you time to act. **If the low air warning comes on while you're driving, stop and park safely as soon as possible**, while you still have control.

## The parking brake control

In newer trucks, the parking brakes are controlled by a **yellow, diamond-shaped knob**. Pull it out to set the parking brakes. Push it in to release them.

Use the parking brakes whenever you park, with two exceptions from the CDL manual:

- Don't set them when the brakes are very hot, such as right after a steep downgrade, because they can be damaged.
- Don't set them when the brakes are wet in freezing weather, because they can freeze. Use wheel chocks instead.

**Key takeaway:** Spring brakes apply at about 20 to 45 psi. When the low air warning comes on, get stopped safely.
""",
            },
            {
                "slug": "inspecting-air-brakes",
                "title": "Inspecting air brakes",
                "quiz": [26, 27, 28, 32],
                "body": """
The air brake check is part of every pre-trip inspection and a key part of the CDL skills test. These are the checks and the numbers to know.

## Air pressure build-up

With the engine at operating speed, pressure should build **from 85 to 100 psi within 45 seconds** on a dual air system. If it takes longer, the compressor or the system may have a problem.

## Governor cut-out and cut-in

Watch the gauge. The compressor should stop pumping at about 125 psi. Then pump the brake pedal to lower the pressure. The compressor should start pumping again at about 100 psi.

## Leakage tests

- **Static test:** engine off, brakes released. After the first drop, a single vehicle should lose **less than 2 psi in one minute**. A combination vehicle should lose less than 3 psi.
- **Applied test:** engine off, brakes fully applied and held. After the first drop, a single vehicle should lose **no more than 3 psi in one minute**. A combination vehicle should lose no more than 4 psi.

## Low air warning and spring brakes

With the engine off, pump the brake pedal to lower the pressure. The low air warning should come on before the pressure drops below 60 psi. Keep pumping. The spring brake control knob should pop out between about 20 and 45 psi.

## Slack adjusters

With the brakes released and the truck chocked, pull hard on each slack adjuster you can reach. **If it moves more than about 1 inch where the push rod attaches, it needs adjustment.** Brakes out of adjustment are one of the most common violations found at roadside inspections.

**Key takeaway:** 45 seconds to build from 85 to 100, less than 2 and 3 psi on the leak tests for a single vehicle, and no more than 1 inch of slack.
""",
            },
            {
                "slug": "braking-on-the-road",
                "title": "Using air brakes on the road",
                "quiz": [31, 34, 36],
                "body": """
Air brakes don't respond instantly, and they can overheat if you use them wrong. These habits keep you in control.

## Brake lag

Air takes time to travel through the lines. It takes **about one-half second** after you press the pedal for the brakes to start working. At highway speed, the truck travels a long way in that half second, which adds to your stopping distance. Leave more room than you think you need.

## Braking on long downgrades

Holding the brakes on all the way down a mountain overheats them. Hot brakes fade and can stop working. The CDL manual teaches **snub braking**:

- Get into a low gear before you start down.
- Once you reach your safe speed, **apply the brakes firmly enough to feel a definite slowdown, until you're about 5 mph below your safe speed. Then release the brakes.**
- When you're back up to your safe speed, repeat.

For example, if your safe speed is 40 mph, brake down to 35 mph, release, and repeat.

## Front brakes

Some drivers used to think front brakes were dangerous on slippery roads. That's wrong. **Front-wheel brakes are good under all conditions**, and they help you stop and stay in control.

## Brake fade and failure

If the brakes feel weak on a grade, slow down, use a lower gear, and look for an escape ramp. If the low air warning comes on, stop and park safely as soon as you can.

**Key takeaway:** Expect about half a second of brake lag, use snub braking on grades, and trust your front brakes.
""",
            },
        ],
    },
    {
        "slug": "combination-vehicles",
        "title": "CDL Combination Vehicles",
        "blurb": "Rollovers, trailer air lines, coupling and uncoupling, and skid control for tractor-trailers.",
        "lessons": [
            {
                "slug": "driving-combinations-safely",
                "title": "Driving combination vehicles safely",
                "quiz": [37, 47, 48],
                "body": """
A tractor-trailer handles differently from a straight truck. It's longer, heavier, and more likely to roll over.

## Rollovers

More than half of truck driver deaths in crashes involve a rollover. Two things raise the risk: a high center of gravity and taking turns too fast.

**The best way to prevent rollovers is to keep the cargo as low as possible and go slowly around turns**, on ramps, and on curves. A truck can tip over at posted ramp speeds, which are set with cars in mind.

## The crack-the-whip effect

When you make a quick steering move, like a sudden lane change, the motion gets stronger toward the back of the rig. That's called rearward amplification. In a set of doubles or triples, **the last trailer is the most likely to roll over.** Steer gently and plan lane changes early.

## Loading doubles and triples

When you pull doubles, **put the heavier trailer first, right behind the tractor.** A heavy trailer at the back makes the rig less stable.

## Off-tracking

On a turn, the rear wheels follow a shorter path than the front wheels. The longer the rig, the more it off-tracks. Watch your mirrors in turns and give yourself room so the trailer doesn't hit curbs, poles, or cars.

**Key takeaway:** Keep cargo low, slow down in turns, steer smoothly, and load the heavier trailer up front.
""",
            },
            {
                "slug": "trailer-air-brakes",
                "title": "Trailer air lines and brakes",
                "quiz": [38, 39, 40, 41],
                "body": """
A trailer's brakes get their air from the tractor through two air lines. You need to know what each part does and how to check it.

## The two air lines

- **Emergency line, also called the supply line:** carries air to the trailer's tanks and controls the trailer's emergency brakes. On most rigs it's **red**.
- **Service line:** carries the air that applies the trailer brakes when you press the brake pedal. On most rigs it's **blue**.

## Glad hands

**Glad hands connect the service and emergency air lines from the tractor to the trailer.** They have rubber seals that keep air from leaking. Check that the seals are in good shape and the glad hands are locked together firmly. Cover unused glad hands so dirt and water can't get in.

## Tractor protection valve

This valve keeps air in the tractor if the trailer breaks away or develops a bad leak. **It closes automatically when air pressure drops to about 20 to 45 psi.** The trailer air supply control, usually a red eight-sided knob in the cab, lets you open and close it yourself.

## The trailer hand valve

The trailer hand valve, also called the trolley valve, applies only the trailer brakes. You use it to test the trailer brakes. **Never use it for parking.** All the air can leak away and the brakes will release. Use the parking brakes instead.

**Key takeaway:** Red is emergency, blue is service, glad hands connect them, and never park using the trolley valve.
""",
            },
            {
                "slug": "coupling-and-uncoupling",
                "title": "Coupling and uncoupling",
                "quiz": [44, 45, 46],
                "body": """
A trailer that isn't coupled correctly can come loose on the highway. Do it the same careful way every time.

## Before you back under

- Inspect the fifth wheel. It should be greased, tilted down toward the rear, and the jaws should be open.
- Make sure the area is clear and the trailer wheels are chocked or the trailer brakes are locked.
- Check the trailer height. **The trailer should be slightly lower than the center of the fifth wheel**, so the trailer is lifted a little as you back under it.

## Coupling

Back up slowly and square to the trailer until the fifth wheel locks onto the kingpin. Then:

- **Test the coupling with a tug test.** Put the tractor in low gear with the trailer brakes locked, and **pull forward gently** to make sure the trailer is locked on.
- **Check the fifth wheel visually.** Get out and look with a flashlight. **There should be no space between the upper and lower fifth wheel.** The locking jaws should be closed around the shank of the kingpin, not the head, and the locking lever should be in the locked position.
- Connect the air lines and the electrical cord, and make sure they won't catch on anything.
- Raise the landing gear all the way and secure the crank handle.

## Uncoupling

Park on firm, level ground in a straight line. Lock the trailer brakes, lower the landing gear until it takes some weight, and disconnect the air lines and electrical cord. Unlock the fifth wheel, then pull the tractor partly out and stop to confirm the trailer is supported before pulling away completely.

**Key takeaway:** Trailer slightly low, tug test in low gear, and no gap between the fifth wheel plates.
""",
            },
            {
                "slug": "skids-and-jackknifes",
                "title": "Skids and jackknifes",
                "quiz": [42, 43],
                "body": """
When the wheels of a tractor-trailer lock up, the rig can fold up like a pocketknife. Knowing why it happens is the best way to prevent it.

## Tractor jackknife

**A tractor jackknife is most often caused by the tractor's drive wheels locking up or skidding**, usually from braking too hard, especially on a slippery road. The back of the tractor slides sideways, and the trailer pushes it around.

## Trailer jackknife

When the trailer's wheels lock up, the trailer can swing out into another lane. This is more likely when the trailer is empty or lightly loaded, because there's less weight holding the tires to the road.

## What to do

- **If the trailer starts to skid, release the brakes** so the tires can grip the road again. Once the tires are rolling, the trailer usually straightens out behind the tractor.
- Don't use the trailer hand brake to try to straighten the rig. That makes the skid worse.
- Brake smoothly and early, and slow down on wet or icy roads.

## Preventing skids

Most skids start with speed that's too high for the conditions or braking that's too hard. Keep more following distance in bad weather so you never have to brake hard.

**Key takeaway:** Locked drive wheels cause tractor jackknifes. If the trailer skids, release the brakes.
""",
            },
        ],
    },
]
