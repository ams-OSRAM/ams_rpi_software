/* SPDX-License-Identifier: BSD-2-Clause */
/*
 * Copyright (C) 2019, Raspberry Pi (Trading) Limited
 *
 * cam_helper_mira130.cpp - camera helper for mira130 sensor
 */

#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

/*
 * We have observed that the mira130 embedded data stream randomly returns junk
 * register values. Do not rely on embedded data until this has been resolved.
 */
#define ENABLE_EMBEDDED_DATA 0

#include "cam_helper.h"
#if ENABLE_EMBEDDED_DATA
#include "md_parser.h"
#endif

using namespace RPiController;

/*
 * We care about one gain register and a pair of exposure registers. Their I2C
 * addresses from the mira130 datasheet:
 */
constexpr uint32_t gainReg = 0x400A;
constexpr uint32_t expHiReg = 0x3E00;
constexpr uint32_t expLoReg = 0x3E02;
constexpr uint32_t frameLengthHiReg = 0x320E;
constexpr uint32_t frameLengthLoReg = 0x320F;
constexpr std::initializer_list<uint32_t> registerList [[maybe_unused]]
	= { expHiReg, expLoReg, gainReg, frameLengthHiReg, frameLengthLoReg };

class CamHelperMira130 : public CamHelper
{
public:
	CamHelperMira130();
	uint32_t gainCode(double gain) const override;
	double gain(uint32_t gain_code) const override;
	unsigned int mistrustFramesModeSwitch() const override;
	bool sensorEmbeddedDataPresent() const override;

private:
	/*
	 * Smallest difference between the frame length and integration time,
	 * in units of lines.
	 */
	static constexpr int frameIntegrationDiff = 4;
	static constexpr float analogGainLut[] = {
	1,
	1.031,
	1.063,
	1.094,
	1.125,
	1.156,
	1.188,
	1.219,
	1.25,
	1.281,
	1.313,
	1.344,
	1.375,
	1.406,
	1.438,
	1.469,
	1.5,
	1.531,
	1.563,
	1.594,
	1.625,
	1.656,
	1.688,
	1.719,
	1.75,
	1.781,
	1.813,
	1.869,
	1.926,
	1.982,
	2.039,
	2.096,
	2.152,
	2.209,
	2.266,
	2.322,
	2.379,
	2.436,
	2.492,
	2.549,
	2.605,
	2.662,
	2.719,
	2.775,
	2.832,
	2.889,
	2.945,
	3.002,
	3.059,
	3.115,
	3.172,
	3.229,
	3.285,
	3.342,
	3.398,
	3.455,
	3.512,
	3.568,
	3.625,
	3.738,
	3.852,
	3.965,
	4.078,
	4.191,
	4.305,
	4.418,
	4.531,
	4.645,
	4.758,
	4.871,
	4.984,
	5.098,
	5.211,
	5.324,
	5.438,
	5.551,
	5.664,
	5.777,
	5.891,
	6.004,
	6.117,
	6.23,
	6.344,
	6.457,
	6.57,
	6.684,
	6.797,
	6.91,
	7.023,
	7.137,
	7.25,
	7.477,
	7.703,
	7.93,
	8.156,
	8.383,
	8.609,
	8.836,
	9.063,
	9.289,
	9.516,
	9.742,
	9.969,
	10.195,
	10.422,
	10.648,
	10.875,
	11.102,
	11.328,
	11.555,
	11.781,
	12.008,
	12.234,
	12.461,
	12.688,
	12.914,
	13.141,
	13.367,
	13.594,
	13.82,
	14.047,
	14.273,
	14.5,
	14.953,
	15.406,
	15.859,
	16.313,
	16.766,
	17.219,
	17.672,
	18.125,
	18.578,
	19.031,
	19.484,
	19.938,
	20.391,
	20.844,
	21.297,
	21.75,
	22.203,
	22.656,
	23.109,
	23.563,
	24.016,
	24.469,
	24.922,
	25.375,
	25.828,
	26.281,
	26.734,
	27.188,
	27.641,
	28.094,
	28.547,
	};

};

CamHelperMira130::CamHelperMira130()
#if ENABLE_EMBEDDED_DATA
	: CamHelper(std::make_unique<MdParserSmia>(registerList), frameIntegrationDiff)
#else
	: CamHelper({}, frameIntegrationDiff)
#endif
{
}

uint32_t CamHelperMira130::gainCode(double gain) const
{
	uint32_t sizeLut = sizeof(analogGainLut) / sizeof(analogGainLut[0]);
	uint32_t gainCode = 0;
	if (gain <= analogGainLut[0]) {
		gainCode = 0;
	} else if (gain >= analogGainLut[sizeLut - 1]) {
		gainCode = (sizeLut - 1);
	} else {
		while (gainCode < sizeLut - 1) {
			if (gain >= analogGainLut[gainCode] && gain < analogGainLut[gainCode+1]) {
				break;
			}
			gainCode++;
		}
	}
	return gainCode;
}

double CamHelperMira130::gain(uint32_t gainCode) const
{
	uint32_t sizeLut = sizeof(analogGainLut) / sizeof(analogGainLut[0]);
	if (gainCode >= sizeLut) {
		gainCode = sizeLut - 1;
	}
	return (double)(analogGainLut[gainCode]);
}


unsigned int CamHelperMira130::mistrustFramesModeSwitch() const
{
	/*
	 * For reasons unknown, we do occasionally get a bogus metadata frame
	 * at a mode switch (though not at start-up). Possibly warrants some
	 * investigation, though not a big deal.
	 */
	return 1;
}

bool CamHelperMira130::sensorEmbeddedDataPresent() const
{
	return ENABLE_EMBEDDED_DATA;
}

// void CamHelperMira130::populateMetadata(const MdParser::RegisterMap &registers,
// 				       Metadata &metadata) const
// {
// 	DeviceStatus deviceStatus;

// 	deviceStatus.shutterSpeed = exposure(registers.at(expHiReg) * 256 + registers.at(expLoReg), deviceStatus.lineLength);
// 	deviceStatus.analogueGain = gain(registers.at(gainReg));
// 	deviceStatus.frameLength = registers.at(frameLengthHiReg) * 256 + registers.at(frameLengthLoReg);

// 	metadata.set("device.status", deviceStatus);
// }

static CamHelper *create()
{
	return new CamHelperMira130();
}

static RegisterCamHelper reg("mira130", &create);

