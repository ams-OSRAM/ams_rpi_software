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

/*
 * We have observed that the mira050 embedded data stream randomly returns junk
 * register values. Do not rely on embedded data until this has been resolved.
 */
#define ENABLE_EMBEDDED_DATA 0

#include "cam_helper.hpp"
#if ENABLE_EMBEDDED_DATA
#include "md_parser.hpp"
#endif

using namespace RPiController;

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
	uint32_t GainCode(double gain) const override;
	double Gain(uint32_t gain_code) const override;
	unsigned int MistrustFramesModeSwitch() const override;
	bool SensorEmbeddedDataPresent() const override;

private:
	/*
	 * Smallest difference between the frame length and integration time,
	 * in units of lines.
	 */
	static constexpr int frameIntegrationDiff = 4;

	void PopulateMetadata(const MdParser::RegisterMap &registers,
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

uint32_t CamHelperMira050::GainCode(double gain) const
{
	return (uint32_t)(256 - 256 / gain);
}

double CamHelperMira050::Gain(uint32_t gain_code) const
{
	return 256.0 / (256 - gain_code);
}

unsigned int CamHelperMira050::MistrustFramesModeSwitch() const
{
	/*
	 * For reasons unknown, we do occasionally get a bogus metadata frame
	 * at a mode switch (though not at start-up). Possibly warrants some
	 * investigation, though not a big deal.
	 */
	return 1;
}

bool CamHelperMira050::SensorEmbeddedDataPresent() const
{
	return ENABLE_EMBEDDED_DATA;
}

void CamHelperMira050::PopulateMetadata(const MdParser::RegisterMap &registers,
				       Metadata &metadata) const
{
	DeviceStatus deviceStatus;

	deviceStatus.shutter_speed = Exposure(registers.at(expReg));
	deviceStatus.analogue_gain = Gain(registers.at(gainReg));

	metadata.Set("device.status", deviceStatus);
}

static CamHelper *Create()
{
	return new CamHelperMira050();
}

static RegisterCamHelper reg("mira050", &Create);
