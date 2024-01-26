/* SPDX-License-Identifier: BSD-2-Clause */
/*
 * Copyright (C) 2019, Raspberry Pi (Trading) Limited
 *
 * cam_helper_mira016.cpp - camera helper for mira016 sensor
 */

#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <algorithm>
#include <cmath>

#include <libcamera/base/log.h>

/*
 * We have observed that the mira016 embedded data stream randomly returns junk
 * register values. Do not rely on embedded data until this has been resolved.
 */
#define ENABLE_EMBEDDED_DATA 0

#include "cam_helper.h"

using namespace RPiController;
using namespace libcamera;
using libcamera::utils::Duration;
using namespace std::literals::chrono_literals;

namespace libcamera
{
	LOG_DECLARE_CATEGORY(IPARPI)
}

/*
 * We care about one gain register and a pair of exposure registers. Their I2C
 * addresses from the mira016 datasheet:
 */
// constexpr uint32_t gainReg = 0x0024;
// constexpr uint32_t expReg = 0x000E;
// constexpr uint32_t frameLengthHiReg = 0x1013;
// constexpr uint32_t frameLengthLoReg = 0x1012;
// constexpr std::initializer_list<uint32_t> registerList [[maybe_unused]] = {expReg, gainReg};

class CamHelperMira016 : public CamHelper
{
public:
	CamHelperMira016();
	uint32_t gainCode(double gain) const override;
	double gain(uint32_t code) const override;
	uint32_t exposureLines(const Duration exposure, const Duration lineLength) const override;
	Duration exposure(uint32_t exposureLines, const Duration lineLength) const override;
	void getDelays(int &exposureDelay, int &gainDelay,
				   int &vblankDelay, int &hblankDelay) const override;

private:
	static constexpr uint32_t minExposureLines = 60; // in us
	/*
	 * Smallest difference between the frame length and integration time,
	 * in units of lines.
	 */
	static constexpr int frameIntegrationDiff = 4;
	/* ROW_LENGTH is microseconds is (ROW_LENGTH * 8 / MIRA_DATA_RATE) */
	static constexpr Duration timePerLine = 1000ns; // time unit is 1 us
};

CamHelperMira016::CamHelperMira016()
	: CamHelper({}, frameIntegrationDiff)
{
}

uint32_t CamHelperMira016::gainCode(double gain) const
{
	// All 8, 10, 12 bit are coarse gain
	if (mode_.bitdepth == 8)
	{
		return std::log2(gain);
	}
	else if (mode_.bitdepth == 10)
	{
		return std::log2(gain);
	}
	else if (mode_.bitdepth == 12)
	{
		return std::log2(gain);
	}
	else
	{
		return (uint32_t)(gain);
	}
}

double CamHelperMira016::gain(uint32_t gainCode) const
{
	// All 8, 10, 12 bit are coarse gain
	if (mode_.bitdepth == 8)
	{
		return std::exp2(gainCode);
	}
	else if (mode_.bitdepth == 10)
	{
		return std::exp2(gainCode);
	}
	else if (mode_.bitdepth == 12)
	{
		return std::exp2(gainCode);
	}
	else
	{
		return (double)(gainCode);
	}
}

uint32_t CamHelperMira016::exposureLines(const Duration exposure,
										 [[maybe_unused]] const Duration lineLength) const
{
	return std::max<uint32_t>(minExposureLines, exposure / timePerLine);
}

Duration CamHelperMira016::exposure(uint32_t exposureLines,
									[[maybe_unused]] const Duration lineLength) const
{
	return std::max<uint32_t>(minExposureLines, exposureLines) * timePerLine;
}

void CamHelperMira016::getDelays(int &exposureDelay, int &gainDelay,
								 int &vblankDelay, int &hblankDelay) const
{
	/* The driver appears to behave as follows: */
	exposureDelay = 2;
	gainDelay = 2;
	vblankDelay = 2;
	hblankDelay = 2;
}

static CamHelper *create()
{
	return new CamHelperMira016();
}

static RegisterCamHelper reg("mira016", &create);
