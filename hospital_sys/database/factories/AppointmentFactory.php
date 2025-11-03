<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use App\Models\Patient;
use App\Models\Staff;

class AppointmentFactory extends Factory
{
    protected $model = \App\Models\Appointment::class;

    public function definition(): array
    {
        return [
            'patient_id' => Patient::factory(),
            'staff_id' => Staff::factory(),
            'appointment_date' => $this->faker->dateTimeBetween('now', '+1 month')->format('Y-m-d'),
            'appointment_time' => $this->faker->time(),
            'status' => $this->faker->randomElement(['scheduled','completed','cancelled']),
        ];
    }
}
