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
	return (uint32_t)(gain);
}

double CamHelperMira050::gain(uint32_t gainCode) const
{
	return (double)(gainCode);
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

