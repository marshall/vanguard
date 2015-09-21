Pin Usage
===

This is a table of pins currently used by the various subsystems and sensors
of the Stratosphere HAB
<table>
    <tr><th>Component</th><th>Label</th><th>BeagleBone Black pin</th></tr>
    <tr><td>eMMC</td><td>eMMC</td><td>P9_11 through P9_21 would be used by the eMMC boot.</td></tr>
    <tr><td>HDMI</td><td>HDMI</td><td>P8_27 through P8_46 would be used by the HDMI interface. </td></tr>
    <tr><td>Camera Cape</td><td>-</td><td>P9_11 - GPIO0_30</td></tr>
    <tr><td>Camera Cape</td><td>-</td><td>P9_17 - GPIO0_5 (I2C1_SCL)</td></tr>
    <tr><td>Camera Cape</td><td>-</td><td>P9_18 - GPIO0_4 (I2C1_SDA)</td></tr>
    <tr><td>Camera Cape</td><td>I2C</td><td>P9_19 - I2C2_SCL</td></tr>
    <tr><td>Camera Cape</td><td>I2C</td><td>P9_20 - I2C2_SDA</td></tr>
    <!-- <tr><td>TNC-Black</td><td>RX</td><td>P9_21 - UART2_TXD</td></tr> -->
    <!-- <tr><td>TNC-Black</td><td>TX</td><td>P9_22 - UART2_RXD</td></tr> -->
    <tr><td>GPS</td><td>RX</td><td>P9_24 - UART1_TXD</td></tr>
    <tr><td>GPS</td><td>TX</td><td>P9_26 - UART1_RXD</td></tr>
    <tr><td>Main battery voltage</td><td>ANALOG (AIN2)</td><td>P9_37</td></tr>
    <tr><td>External thermistor</td><td>ANALOG (AIN0)</td><td>P9_39</td></tr>
    <tr><td>Internal thermistor</td><td>ANALOG (AIN1) </td><td>P9_40</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_20</td><td>P9_41 - CAM_MCLK</td></tr>
    <tr><td>Camera Cape</td><td>SPI1_CS1</td><td>P9_42 - DMAR</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_38</td><td>P8_3 - GPMC_AD6</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_39</td><td>P8_4 - GPMC_AD7</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_34</td><td>P8_5 - GPMC_AD2</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_35</td><td>P8_6 - GPMC_AD3</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_66</td><td>P8_7 - GPMC_nADV_ALE</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_67</td><td>P8_8 - GPMC_nOE</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_68</td><td>P8_10 - GPMC_nWE</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_45</td><td>P8_11 - GPMC_AD13</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_44</td><td>P8_12 - GPMC_AD12</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_23</td><td>P8_13 - GPMC_AD9</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_26</td><td>P8_14 - GPMC_AD10</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_47</td><td>P8_15 - GPMC_AD15</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_46</td><td>P8_16 - GPMC_AD14</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_27</td><td>P8_17 - GPMC_AD11</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_65</td><td>P8_18 - GPMC_CLK</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_22</td><td>P8_19 - GPMC_AD8</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_62</td><td>P8_21 - GPMC_nCS1</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_37</td><td>P8_22 - GPMC_AD5</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_36</td><td>P8_23 - GPMC_AD4</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_33</td><td>P8_24 - GPMC_AD1</td></tr>
    <tr><td>Camera Cape</td><td>GPIO_32</td><td>P8_25 - GPMC_AD0</td></tr>
    <tr><td>5V-3.3V serial bidirectional voltage level shifter enable</td><td>LSF0204 (EN)</td><td>P8_26 - GPMC_CSN0</td></tr>
    <!--<tr><td>XTEND900</td><td>RX (DI) (GPIO_78)</td><td>P8_37 - TX5</td></tr>
    <tr><td>XTEND900</td><td>TX (DO) (GPIO_79)</td><td>P8_38 - RX5</td></tr> -->
    <tr><td>Modem UART TX</td><td> (GPIO_78)</td><td>P8_37 - TX5</td></tr>
    <tr><td>Modem UART RX</td><td> (GPIO_79)</td><td>P8_38 - RX5</td></tr>
    <!--    <tr><td>Audio</td><td>I2C2_SCL</td><td>P9_19</td></tr>
    <tr><td>Audio</td><td>I2C2_SDA</td><td>P9_20</td></tr>
    <tr><td>Audio</td><td>AUD_MCLK</td><td>P9_25</td></tr>
    <tr><td>Audio</td><td>AUD_DOUT</td><td>P9_28</td></tr>
    <tr><td>Audio</td><td>AUD_WCLK</td><td>P9_29</td></tr>
    <tr><td>Audio</td><td>AUD_DIN</td><td>P9_30</td></tr>
    <tr><td>Audio</td><td>AUD_BCLK</td><td>P9_31</td></tr> -->
    <tr><td>Modem</td><td>TXD</td><td>P9_25 (GPIO3_21) </td></tr>
    <tr><td>Modem</td><td>M0</td><td>P9_28 (GPIO3_17)</td></tr>
    <tr><td>Modem</td><td>M1</td><td>P9_29 (GPIO3_15)</td></tr>
    <tr><td>Modem</td><td>TX_RETIME</td><td>P9_30 (GPIO3_16)</td></tr>
    <tr><td>Modem</td><td>Power (key) TX2H</td><td>P9_31 (GPIO3_14, SPI1_SCLK)</td></tr>
    <tr><td>Modem</td><td>DET</td><td>P9_39 (AIN0)</td></tr> <!-- 39 and 40 are ADC input pins - but they can sense voltage -->
    <tr><td>Low Voltage Alarm Assert</td><td>GPIO1_17</td><td>P9_23</td></tr>

</table>
