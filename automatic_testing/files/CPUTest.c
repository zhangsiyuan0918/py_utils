/***********************************************************************//**
 
 \file    CPU_TEST.c
 
 \brief   CPU test for v850 (prepared for OS use)
 Module prefix: CPU_TEST
 Project:       Power Line Communication
 Controller:    See GHS_Port.h
 Compiler:      See GHS_Port.h


 ***************************************


 \author  kostov01
 
 \date    3.07.2012
 
 \note    (C) Copyright Leopold Kostal GmbH&Co KG \n\n
 Contents and presentations are protected world-wide.\n
 Any kind of using, copying etc. is prohibited without prior permission. \n
 All rights - incl. industrial property rights - are reserved.

 ****************************************************************************/

/******************************************************************************\
 * Version check                                                              *
 * v1.0:  3.07.2012 - Initial release                                         *
 * v1.1:  01.11.2012 - review fixes                                           *
 \******************************************************************************/

/******************************************************************************\
 * Includes                                                                   *
 \******************************************************************************/
#include "CPUTest.h"
#include "SystemCheck.h"
#include "IFM_For_Rte.h"
 //Added to fixQAC Warning :A function shall not be declared implicitly
#include "CPUTest_If.h"

/******************************************************************************\
 * Module global variables                                                    *
 \******************************************************************************/
/*PRQA S 2711,1253 EOF*/ /*register keyword*/
/******************************************************************************\
 * Module local variables                                                    *
 \******************************************************************************/
#define CDD_START_SEC_VAR_INIT_UNSPECIFIED
#include "MemMap.h"

static uint32 const cu32AA = 0xAAAAAAAAUL;
static uint32 const cu3255 = 0x55555555UL;
static uint32 const cu32FF = 0xFFFFFFFFUL;

/* = 5*7*11*13*17*19*23*29 */
static uint32 const cu32MulTo29 = 1078282205UL;
static uint32 const cu32MulTo23 = 37182145UL;
static uint32 const cu32MulTo19 = 1616615UL;

#define CDD_STOP_SEC_VAR_INIT_UNSPECIFIED
#include "MemMap.h"

#define CPUT_CONST_3  3
#define CPUT_CONST_29 29
#define CPUT_CONST_23 23
#define CPUT_CONST_16 16
#define CPUT_CONST_19 19
#define CPUT_CONST_437 437
#define CPUT_CONST_LA 0xAAAA0000UL
#define CPUT_CONST_L0 0x0000AAAAUL

boolean CoreTestError = 0;

/******************************************************************************\
 * Definition of module local functions                                      *
 \******************************************************************************/
#define CDD_START_SEC_CODE
#include "MemMap.h"

static Std_ReturnType CpuTest_AluArith(uint32 u32Mul29, uint32 u32Mul23,uint32 u32Mul19, uint32 u32AA);
static Std_ReturnType CpuTest_AluLogical(uint32 u32FF, uint32 u32AA,uint32 u3255);

/******************************************************************************\
 * CpuTest_AluLogical
 * Implements simple CPU logical test.
 * The compiler optimizer is too efficient and generates no code if we
 * use the ff aa & 55 patterns directly in the body of the function.
 * Thus these constants are passed as parameters. This is confusing but
 * guarantees that the code will be generated, no matter what optimizations
 * the compiler is run with.
 *
 * \return E_OK  - TEST is passed correctly
 *         E_NOT_OK - TEST is not passed
 *  
 * \param  u32FF - 0xFFFFFFFF pattern
 *         u32AA - 0xAAAAAAAA pattern
 *         u3255 - 0x55555555 pattern
 * 
 * \author kostov01
 \******************************************************************************/
static Std_ReturnType CpuTest_AluLogical(uint32 u32FF, uint32 u32AA,
        uint32 u3255)
{
    Std_ReturnType Result = E_OK;
    register uint32 u32Res = 0x0UL;
    register uint8 u8Cnt = 0;

    for (u8Cnt = 0; (u8Cnt < CPUT_CONST_3) && (Result != E_NOT_OK); u8Cnt++)
    {

        /* simple AND test */
        u32Res = (u32FF & u32AA);
        if (u32Res != cu32AA)
        {
            Result = E_NOT_OK;
        }

        /* simple AND test */
        u32Res = (~u32FF & u32AA);
        if (u32Res != 0UL)
        {
            Result = E_NOT_OK;
        }

        /* simple OR test */
        u32Res = (u32FF | u32AA);
        if (u32Res != cu32FF)
        {
            Result = E_NOT_OK;
        }

        /* simple OR test */
        u32Res = (u32FF & u32AA);
        u32Res = (~u32Res | u32AA);
        if (u32Res != cu32FF)
        {
            Result = E_NOT_OK;
        }

        /* simple XOR test */
        u32Res = (u32AA ^ u3255);
        if (u32Res != cu32FF)
        {
            Result = E_NOT_OK;
        }

        /* simple XOR test */
        u32Res = (u32AA ^ u32FF);
        if (u32Res != cu3255)
        {
            Result = E_NOT_OK;
        }
    }

    return Result;
}

/******************************************************************************\
 * CpuTest_AluArith
 * Implements simple CPU arithmetic test.
 *
 * The compiler optimizer is too efficient and generates no code if we
 * use the patterns constants directly in the body of the function.
 * Thus these constants are passed as parameters. This is confusing but
 * guarantees that the code will be generated, no matter what optimizations
 * the compiler is run with.
 *
 * \return E_OK  - CPU is calculating correctly
 *         E_NOT_OK - CPU is NOT calculating correctly
 *
 * \param  u32Mul29 - the cu32MulTo29 constant = 5*7*11*13*17*19*23*29
 *         u32Mul23 - cuMulTo23 = 5*7*11*13*17*19*23
 *         u32Mul19 - cuMulTo19 = 5*7*11*13*17*19
 *         u32AA    - the 0xAAAAAAAA pattern
 *
 * \author kostov01
 \******************************************************************************/
static Std_ReturnType CpuTest_AluArith(uint32 u32Mul29, uint32 u32Mul23,
        uint32 u32Mul19, uint32 u32AA)
{
    Std_ReturnType Result = E_OK;
    register uint32 u32Res = 0x0UL;
    register uint8 u8Cnt = 0;
    register uint8 u8ShiftCnt = 0;

    for (u8Cnt = 0; (u8Cnt < CPUT_CONST_3) && (Result != E_NOT_OK); u8Cnt++)
    {

        /* Simple multiplication test */
        u32Res = u32Mul19 * CPUT_CONST_23;
        if (u32Res != cu32MulTo23)
        {
            Result = E_NOT_OK;
        }
        else
        {
            /* OK */
        }

        /* Simple multiplication test */
        u32Res = u32Mul19 * CPUT_CONST_23 * CPUT_CONST_29;
        if (u32Res != cu32MulTo29)
        {
            Result = E_NOT_OK;
        }
        else
        {
            /* OK */
        }

        /* Simple division test */
        u32Res = u32Mul29 / CPUT_CONST_29;
        if (u32Res != cu32MulTo23)
        {
            Result = E_NOT_OK;
        }
        else
        {
            /* OK */
        }

        /* Simple division test */
        u32Res = (u32Mul29 / CPUT_CONST_29) / CPUT_CONST_23;
        if (u32Res != cu32MulTo19)
        {
            Result = E_NOT_OK;
        }
        else
        {
            /* OK */
        }

        /* Check logical shift left */
        u32Res = u32AA;
        if ((u32Res << CPUT_CONST_16) != CPUT_CONST_LA)
        {
            Result = E_NOT_OK;
        }
        else
        {
            /* OK */
        }

        /* Check logical shift right */
        u32Res = u32AA;
        if ((u32Res >> CPUT_CONST_16) != CPUT_CONST_L0)
        {
            Result = E_NOT_OK;
        }
        else
        {
            /* OK */
        }

        /* Do the 19*23 calculation using add only*/
        u32Res = 0;
        for (u8ShiftCnt = 0; u8ShiftCnt < CPUT_CONST_23; u8ShiftCnt++)
        {
            u32Res += CPUT_CONST_19;
        }

        if (u32Res != CPUT_CONST_437)
        {
            Result = E_NOT_OK;
        }
        else
        {
            /* OK */
        }

        /* Do the 437/19 = 23 math using sub only */
        for (u8ShiftCnt = 0; u8ShiftCnt < CPUT_CONST_19; u8ShiftCnt++)
        {
            u32Res -= CPUT_CONST_23;
        }

        if (u32Res != 0)
        {
            Result = E_NOT_OK;
        }
        else
        {
            /* OK */
        }

    }

    return Result;
}/*PRQA S 6110,6130*/ /*metrics not important for CPU test*/


#define CDD_STOP_SEC_CODE
#include "MemMap.h"

/******************************************************************************\
 * Definition of module global functions                                      *
 \******************************************************************************/
#define CDD_START_SEC_CODE
#include "MemMap.h"
/******************************************************************************\
 * CpuTest_Check
 * Implements simple CPU test. IS_SW_ARCH_LIM_1256.1
 *
 * \return E_OK  - CRC is correctly calculated
 *         E_NOT_OK - CRC is not calculated because of invalid parameters
 *
 * \param  void
 *
 * \author kostov01
 \******************************************************************************/
Std_ReturnType CpuTest_Check(void)
{
    Std_ReturnType Result= E_OK;

    Result = CpuTest_AluLogical( cu32FF, cu32AA, cu3255 );
    Result |= CpuTest_AluArith( cu32MulTo29, cu32MulTo23, cu32MulTo19, cu32AA );

    return Result;
}

/* Perform Core test*/
boolean CoreTest_Error_Check(void)
{

	if(CPUTest_If_Execute_Test())
	{
		CoreTestError = E_NOT_OK;
		sSysChk_Main.sCpuTestData.tCorTestResult = E_NOT_OK;
/*    	IFM_NotifyFaultEvent(IFM_SYS_Failure_CoreTest_Main, IFM_FaultEvent_Set);*/
	}
	else
	{
		CoreTestError = E_OK;
		sSysChk_Main.sCpuTestData.tCorTestResult = E_OK;
/*    	IFM_NotifyFaultEvent(IFM_SYS_Failure_CoreTest_Main, IFM_FaultEvent_Cleared);*/
	}
  return (CoreTestError);
}


#define CDD_STOP_SEC_CODE
#include "MemMap.h"
