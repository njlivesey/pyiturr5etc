"""A module for performing link budget calculations"""

import numpy as np
import pint
import intervaltree

# Do some setup on the pint unit registry
ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
ureg.default_format = "~P"
ureg.define("decibelwatt = watt; logbase: 10; logfactor: 10 = dBW")


def antenna_gain(
    *,
    frequency: pint.Quantity,
    diameter: pint.Quantity,
    efficiency: float = None,
) -> pint.Quantity:
    """Compute antenna gain for given parameters"""
    if efficiency is None:
        efficiency = 1.0
    wavelength = ureg.speed_of_light / frequency
    return ((np.pi * diameter / wavelength) ** 2 * efficiency).to(ureg.dB)


def friis_loss(
    *,
    frequency: pint.Quantity,
    separation: pint.Quantity,
) -> pint.Quantity:
    """Compute the Friis loss for a link budget"""
    return ((4 * np.pi * separation * frequency / ureg.speed_of_light) ** 2).to(ureg.dB)


def range_from_frequency_and_width(
    *, frequency: pint.Quantity, bandwidth: pint.Quantity
) -> slice:
    """Convert a center frequency and bandwidth to a frequency range"""
    return slice(
        frequency - 0.5 * bandwidth,
        frequency + 0.5 * bandwidth,
    )


def overlapping_frequency_range(range_a: slice, range_b: slice) -> slice:
    """Compute the overlapping range between two bands"""
    max_start = max(range_a.start, range_b.start)
    min_stop = min(range_a.stop, range_b.stop)
    if max_start > min_stop:
        return None
    else:
        return slice(max_start, min_stop)


def beam_length(
    *,
    incidence_angle: pint.Quantity,
    orbit_altitude: pint.Quantity,
    planet_radius: pint.Quantity = None,
) -> pint.Quantity:
    """Compute the distance from the observer to the observed point"""
    if planet_radius is None:
        planet_radius = 6_371 * ureg.km
    # Probably a better way to do this but here we go.  First invoke the sine rule to
    # get the angle between the view direction and spacecraft nadir.  The sine rule
    # ratios are equal to twice the radius of the circumcircle.
    interior_angle = 180 * ureg.deg - incidence_angle
    two_r = (planet_radius + orbit_altitude) / np.sin(interior_angle)
    nadir_angle = np.arcsin(planet_radius / two_r)
    # Now compute the angle between spacracraft nadir and observation location at the
    # center of the planet
    center_angle = 180.0 * ureg.deg - interior_angle - nadir_angle
    # Now use the sine rule to get the viewing distance
    viewing_distance = np.sin(center_angle) * two_r
    return viewing_distance


def link_budget(
    *,
    frequency: pint.Quantity,
    source_frequency_range: slice = None,
    source_max_power: pint.Quantity = None,
    source_max_psd: pint.Quantity = None,
    source_gain: pint.Quantity = None,
    separation: pint.Quantity,
    receiver_gain: pint.Quantity = None,
    receiver_diameter: pint.Quantity = None,
    receiver_efficiency: float = None,
    receiver_frequency_range: slice = None,
    result_unit: pint.Unit = None,
    return_details: bool = False,
) -> pint.Quantity:
    """Compute the end-to-end link budget, typically for RFI situations"""
    # First compute the source power.  If we have a psd then ponder that
    notes = []
    if source_max_psd is not None and source_frequency_range is not None:
        source_bandwidth = source_frequency_range.stop - source_frequency_range.start
        psd_based_power = source_max_psd * source_bandwidth
        notes.append(
            f"Computed psd-based total source power as {psd_based_power.to(ureg.dBm):.2f~P}"
        )
        if source_max_power is not None:
            if psd_based_power > source_max_power:
                notes.append(
                    f"Limiting power to stated maximum of {source_max_power.to(ureg.dBm):.2f~P}"
                )
            source_power = min(source_max_power, psd_based_power)
        else:
            notes.append("Using this as source power")
            source_power = psd_based_power
    else:
        notes.append("Using this as source power")
        source_power = source_max_power
    # Now consider the antenna gain for the source
    if source_gain is None:
        source_gain = 0.0 * ureg.dB
    notes.append(f"Source gain is {source_gain.to(ureg.dB):.2f~P}")
    # Now consider the path loss
    path_loss = friis_loss(frequency=frequency, separation=separation)
    notes.append(f"Path loss is {path_loss.to(ureg.dB):.2f~P}")
    # Now consider the receiver antenna gain
    if receiver_gain is None:
        receiver_gain = antenna_gain(
            frequency=frequency,
            diameter=receiver_diameter,
            efficiency=receiver_efficiency,
        )
    notes.append(f"Receiver gain is {receiver_gain.to(ureg.dB):.2f~P}")
    # Now consider the reciever bandwidth
    if receiver_frequency_range is not None:
        if source_frequency_range is not None:
            spectral_overlap = overlapping_frequency_range(
                source_frequency_range, receiver_frequency_range
            )
        else:
            spectral_overlap = receiver_frequency_range
        received_bandwidth = spectral_overlap.stop - spectral_overlap.start
        notes.append(f"Received bandwidth is {received_bandwidth.to(ureg.MHz):.2f~P}")
        # Possibly limit the power in light of the maximum allowed PSD
        implied_psd = source_power / received_bandwidth
        if implied_psd > source_max_psd:
            source_power = source_max_psd * received_bandwidth
            notes.append(
                f"Limiting transmitted power to {source_power.to(ureg.dBm):.2f~P} in light of implied PSD"
            )
    # Don't think I need to consider any kind of bandwidth "gain" do I?
    received_power = (
        source_power.to(ureg.W)
        * source_gain.to(ureg.dimensionless)
        / path_loss.to(ureg.dimensionless)
        * receiver_gain.to(ureg.dimensionless)
    )
    if result_unit is None:
        result_unit = ureg.dBW
    received_power = received_power.to(result_unit)
    notes.append(f"Received power is: {received_power:.2f~P}")
    # Possibly put all the interim results in a dict
    if return_details:
        notes = "\n".join(notes)
        variables = [
            "source_bandwidth",
            "psd_based_power",
            "source_power",
            "path_loss",
            "receiver_gain",
            "spectral_overlap",
            "received_bandwidth",
            "implied_psd",
            "notes",
        ]
        details = {}
        for variable in variables:
            try:
                details[variable] = eval(variable)
            except NameError:
                details[variable] = None
        return received_power, details
    return received_power
