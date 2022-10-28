/* SPDX-License-Identifier: BSD-2-Clause */
/*
 * Copyright (C) 2019, Raspberry Pi (Trading) Limited
 *
 * cam_helper_mira050.cpp - camera helper for mira050 sensor
 */

#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <algorithm>
#include <cmath>

/*
 * We have observed that the mira050 embedded data stream randomly returns junk
 * register values. Do not rely on embedded data until this has been resolved.
 */
#define ENABLE_EMBEDDED_DATA 0

#include "cam_helper.h"
#if ENABLE_EMBEDDED_DATA
#include "md_parser.h"
#endif

using namespace RPiController;
using libcamera::utils::Duration;
using namespace std::literals::chrono_literals;

/*
 * We care about one gain register and a pair of exposure registers. Their I2C
 * addresses from the mira050 datasheet:
 */
constexpr uint32_t gainReg = 0x0024;
constexpr uint32_t expReg = 0x000E;
// constexpr uint32_t frameLengthHiReg = 0x1013;
// constexpr uint32_t frameLengthLoReg = 0x1012;
constexpr std::initializer_list<uint32_t> registerList [[maybe_unused]]
	= { expReg, gainReg };

class CamHelperMira050 : public CamHelper
{
public:
	CamHelperMira050();
	uint32_t gainCode(double gain) const override;
	double gain(uint32_t code) const override;
	uint32_t exposureLines(Duration exposure) const override;
	Duration exposure(uint32_t exposureLines) const override;
	unsigned int mistrustFramesModeSwitch() const override;
	bool sensorEmbeddedDataPresent() const override;

private:
	/*
	 * Smallest difference between the frame length and integration time,
	 * in units of lines.
	 */
	static constexpr int frameIntegrationDiff = 4;
	/* ROW_LENGTH is microseconds is (ROW_LENGTH * 8 / MIRA_DATA_RATE) */
	static constexpr Duration timePerLine = (2417.0 * 8.0 / 1000.0) / 1.0e6 * 1.0s;
	static constexpr float gainLut8bit[] = {
	1,
	1.018,
	1.056,
	1.075,
	1.118,
	1.14,
	1.188,
	1.213,
	1.267,
	1.295,
	1.326,
	1.373,
	1.425,
	1.462,
	1.5,
	1.541,
	1.583,
	1.652,
	1.701,
	1.727,
	1.781,
	1.839,
	1.9,
	1.966,
	2,
	2.073,
	2.151,
	2.192,
	2.28,
	2.327,
	2.426,
	2.478,
	2.533,
	2.651,
	2.714,
	2.78,
	2.886,
	2.961,
	3.04,
	3.167,
	3.257,
	3.353,
	3.455,
	3.563,
	3.619,
	3.738,
	3.864,
	4,
	4.071,
	4.222,
	4.302,
	4.471,
	4.56,
	4.75,
	4.851,
	5.067,
	5.182,
	5.302,
	5.494,
	5.7,
	5.846,
	6,
	6.247,
	6.423,
	6.609,
	6.806,
	7.015,
	7.238,
	7.355,
	7.6,
	7.862,
	8.143,
	8.291,
	8.604,
	8.769,
	9.12,
	9.306,
	9.702,
	9.913,
	10.133,
	10.605,
	10.857,
	11.259,
	11.544,
	11.844,
	12.324,
	12.667,
	13.029,
	13.412,
	13.818,
	14.25,
	14.71,
	14.951,
	15.458,
	16,
	};

	void populateMetadata(const MdParser::RegisterMap &registers,
			      Metadata &metadata) const override;
};

CamHelperMira050::CamHelperMira050()
#if ENABLE_EMBEDDED_DATA
	: CamHelper(std::make_unique<MdParserSmia>(registerList), frameIntegrationDiff)
#else
	: CamHelper({}, frameIntegrationDiff)
#endif
{
}

uint32_t CamHelperMira050::gainCode(double gain) const
{
	if (mode_.bitdepth == 12) {
		return std::log2(gain);
	} else if (mode_.bitdepth == 8) {
		uint32_t sizeLut = sizeof(gainLut8bit) / sizeof(gainLut8bit[0]);
		uint32_t i = 0;
		if (gain <= gainLut8bit[0]) {
			return 0;
		}
		while (i < sizeLut - 1) {
			if (gain > gainLut8bit[i] && gain < gainLut8bit[i+1]) {
				break;
			}
			i++;
		}
		return (uint32_t)(i);
	} else {
		return (uint32_t)(gain);
	}
}

double CamHelperMira050::gain(uint32_t gainCode) const
{
	if (mode_.bitdepth == 12) {
		return std::exp2(gainCode);
	} else if (mode_.bitdepth == 8){
		uint32_t sizeLut = sizeof(gainLut8bit) / sizeof(gainLut8bit[0]);
		if (gainCode >= sizeLut) {
			gainCode = sizeLut - 1;
		}
		return (double)(gainLut8bit[gainCode]);
	} else {
		return (double)(gainCode);
	}
}

uint32_t CamHelperMira050::exposureLines(Duration exposure) const
{
	return (uint32_t)(exposure / timePerLine);
}

Duration CamHelperMira050::exposure(uint32_t exposureLines) const
{
	return (exposureLines * timePerLine);
}


unsigned int CamHelperMira050::mistrustFramesModeSwitch() const
{
	/*
	 * For reasons unknown, we do occasionally get a bogus metadata frame
	 * at a mode switch (though not at start-up). Possibly warrants some
	 * investigation, though not a big deal.
	 */
	return 1;
}

bool CamHelperMira050::sensorEmbeddedDataPresent() const
{
	return ENABLE_EMBEDDED_DATA;
}

void CamHelperMira050::populateMetadata(const MdParser::RegisterMap &registers,
				       Metadata &metadata) const
{
	DeviceStatus deviceStatus;

	deviceStatus.shutterSpeed = exposure(registers.at(expReg));
	deviceStatus.analogueGain = gain(registers.at(gainReg));

	metadata.set("device.status", deviceStatus);
}

static CamHelper *create()
{
	return new CamHelperMira050();
}

static RegisterCamHelper reg("mira050", &create);

